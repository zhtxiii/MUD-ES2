// sword.c

#include <weapon.h>

#ifdef AS_FEATURE
#include <dbase.h>
#else
inherit EQUIP;
#endif

varargs void init_sword(int damage, int flag)
{
	mixed action_func;

	if( clonep(this_object()) ) return;

	set("weapon_prop/damage", damage);
	set("flag", (int)flag | EDGED);
	set("skill_type", "sword");
	if( !query("actions") ) {
		// Fix for warning: Expression has no side effects
		action_func = (: WEAPON_D, "query_action" :);
		set("actions", action_func);
		set("verbs", ({ "slash", "slice", "thrust" }) );
	}
}

