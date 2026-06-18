
string chinese_number(int i)
{
	return CHINESE_D->chinese_number(i);
}

string to_chinese(string str)
{
	return CHINESE_D->chinese(str);
}

int utf8_byte(int b)
{
  return b < 0 ? b + 256 : b;
}

int is_chinese(string str)
{
  int i, b0, b1, b2;
  int len = strlen(str);
  // UTF-8 字节语义：CJK 统一汉字 U+4E00-U+9FFF 编码为 3 字节，
  // 首字节 0xE4-0xE9，后两字节为延续字节 (10xxxxxx)。
  for(i=0; i+2<len; i++) {
      b0 = utf8_byte(str[i]);
      b1 = utf8_byte(str[i+1]);
      b2 = utf8_byte(str[i+2]);
      if (b0 >= 0xE4 && b0 <= 0xE9
          && (b1 & 0xC0) == 0x80
          && (b2 & 0xC0) == 0x80) return 1;
  }
  return 0;
}

int utf8_strlen(string str)
{
  int i, b;
  int n = 0;
  int len = strlen(str);
  for(i=0; i<len; i++) {
    b = utf8_byte(str[i]);
    if ((b & 0xC0) != 0x80) n++;
  }
  return n;
}
