#!/bin/bash

set -u

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$(dirname "$DIR")"

PID_FILE="${DIR}/keepmud.pid"
MUD_PID_FILE="${DIR}/mudos.pid"
STOP_FILE="${DIR}/keepmud.stop"
LOG_FILE="${DIR}/keepmud.log"
RESTART_DELAY="${RESTART_DELAY:-5}"

usage() {
  cat <<EOF
Usage: $0 {start|stop|restart|status|run}

Commands:
  start    Start MUD under a watchdog and restart it after crash/exit.
  stop     Stop the watchdog and the running MUD, then prevent restart.
  restart  Stop everything, then start the watchdog again.
  status   Show watchdog and MUD process status.
  run      Run watchdog in the foreground. Usually used internally.

Environment:
  RESTART_DELAY  Seconds to wait before restarting MUD. Default: 5.
EOF
}

is_running() {
  local pid="${1:-}"
  [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null
}

read_pid() {
  local file="$1"
  [[ -f "$file" ]] && sed -n '1p' "$file"
}

find_watchdog_pids() {
  ps -eo pid=,args= | awk -v self="$$" -v script="${DIR}/keepmud.sh" '
    $1 != self &&
    ($2 ~ /(^|\/)(bash|sh)$/) &&
    (($3 == script) || ($3 ~ /(^|\/)keepmud\.sh$/)) &&
    ($4 == "run") { print $1 }
  '
}

find_mud_pids() {
  local driver
  driver="$(driver_path)"
  [[ -n "$driver" ]] && ps -eo pid=,args= | awk -v self="$$" -v driver="$driver" -v config="${DIR}/config.ES2" '
    $1 != self && $2 == driver && $3 == config { print $1 }
  '
}

write_config() {
  sed -e "s%__ROOT__%${ROOT_DIR}%g" "${DIR}/config.ES2.in" > "${DIR}/config.ES2"
}

driver_path() {
  local unamestr
  unamestr="$(uname)"
  if [[ "$unamestr" == "Linux" ]]; then
    echo "${DIR}/linux/driver"
  elif [[ "$unamestr" == "Darwin" ]]; then
    echo "${DIR}/osx/driver"
  else
    echo ""
  fi
}

stop_pid_file() {
  local file="$1"
  local pid
  pid="$(read_pid "$file")"

  if ! is_running "$pid"; then
    rm -f "$file"
    return 0
  fi

  kill "$pid" 2>/dev/null || true

  local i
  for i in {1..20}; do
    if ! is_running "$pid"; then
      rm -f "$file"
      return 0
    fi
    sleep 0.5
  done

  kill -9 "$pid" 2>/dev/null || true
  rm -f "$file"
}

stop_pids() {
  local pid
  for pid in "$@"; do
    if is_running "$pid"; then
      kill "$pid" 2>/dev/null || true
    fi
  done

  local i
  for i in {1..20}; do
    local any_running=0
    for pid in "$@"; do
      if is_running "$pid"; then
        any_running=1
        break
      fi
    done

    [[ "$any_running" -eq 0 ]] && return 0
    sleep 0.5
  done

  for pid in "$@"; do
    if is_running "$pid"; then
      kill -9 "$pid" 2>/dev/null || true
    fi
  done
}

start_watchdog() {
  local pid mud_pid watchdog_pids
  pid="$(read_pid "$PID_FILE")"
  mud_pid="$(read_pid "$MUD_PID_FILE")"
  watchdog_pids="$(find_watchdog_pids)"

  if is_running "$pid" || [[ -n "$watchdog_pids" ]]; then
    echo "keepmud watchdog is already running: $pid"
    return 0
  fi

  if is_running "$mud_pid"; then
    echo "stopping unmanaged MUD process before starting watchdog: $mud_pid"
    stop_pid_file "$MUD_PID_FILE"
  fi

  rm -f "$STOP_FILE" "$PID_FILE"
  nohup "$0" run >> "$LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"
  echo "keepmud watchdog started: $!"
  echo "log: $LOG_FILE"
}

stop_all() {
  touch "$STOP_FILE"

  local watchdog_pid mud_pids watchdog_pids
  watchdog_pid="$(read_pid "$PID_FILE")"
  mud_pids="$(find_mud_pids)"
  watchdog_pids="$(find_watchdog_pids)"

  stop_pid_file "$MUD_PID_FILE"
  if [[ -n "$mud_pids" ]]; then
    stop_pids $mud_pids
  fi

  if is_running "$watchdog_pid" && [[ "$watchdog_pid" != "$$" ]]; then
    stop_pid_file "$PID_FILE"
  else
    rm -f "$PID_FILE"
  fi
  if [[ -n "$watchdog_pids" ]]; then
    stop_pids $watchdog_pids
  fi

  rm -f "$MUD_PID_FILE"
  echo "MUD service stopped. Restart is disabled until start/restart is used."
}

status() {
  local watchdog_pid mud_pid watchdog_pids mud_pids
  watchdog_pid="$(read_pid "$PID_FILE")"
  mud_pid="$(read_pid "$MUD_PID_FILE")"
  watchdog_pids="$(find_watchdog_pids)"
  mud_pids="$(find_mud_pids)"

  if is_running "$watchdog_pid" || [[ -n "$watchdog_pids" ]]; then
    echo "watchdog: running (${watchdog_pid:-$watchdog_pids})"
  else
    echo "watchdog: stopped"
  fi

  if is_running "$mud_pid" || [[ -n "$mud_pids" ]]; then
    echo "mud: running (${mud_pid:-$mud_pids})"
  else
    echo "mud: stopped"
  fi

  if [[ -f "$STOP_FILE" ]]; then
    echo "restart: disabled by stop marker"
  else
    echo "restart: enabled"
  fi
}

run_watchdog() {
  echo $$ > "$PID_FILE"
  rm -f "$STOP_FILE"

  trap 'touch "$STOP_FILE"; stop_pid_file "$MUD_PID_FILE"; rm -f "$PID_FILE"; exit 0' INT TERM

  while [[ ! -f "$STOP_FILE" ]]; do
    local driver
    driver="$(driver_path)"

    if [[ -z "$driver" ]]; then
      echo "Unsupported OS: $(uname)" >&2
      exit 1
    fi

    if [[ ! -x "$driver" ]]; then
      echo "Driver is not executable: $driver" >&2
      exit 1
    fi

    write_config
    export LD_LIBRARY_PATH="${HOME}/lib:${LD_LIBRARY_PATH:-}"

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] starting MUD: $driver ${DIR}/config.ES2"
    "$driver" "${DIR}/config.ES2" &
    echo $! > "$MUD_PID_FILE"

    wait "$(cat "$MUD_PID_FILE")"
    local exit_code=$?
    rm -f "$MUD_PID_FILE"

    if [[ -f "$STOP_FILE" ]]; then
      break
    fi

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] MUD exited with code ${exit_code}; restarting in ${RESTART_DELAY}s"
    sleep "$RESTART_DELAY"
  done

  rm -f "$PID_FILE" "$MUD_PID_FILE"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] watchdog stopped"
}

case "${1:-}" in
  start)
    start_watchdog
    ;;
  stop)
    stop_all
    ;;
  restart)
    stop_all
    start_watchdog
    ;;
  status)
    status
    ;;
  run)
    run_watchdog
    ;;
  *)
    usage
    exit 1
    ;;
esac
