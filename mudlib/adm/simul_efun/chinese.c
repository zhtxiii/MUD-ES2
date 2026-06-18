
string chinese_number(int i)
{
	return CHINESE_D->chinese_number(i);
}

string to_chinese(string str)
{
	return CHINESE_D->chinese(str);
}

int is_chinese(string str)
{
  int i, b0, b1, b2;
  int len = strlen(str);
  // UTF-8 字节语义：CJK 统一汉字 U+4E00-U+9FFF 编码为 3 字节，
  // 首字节 0xE4-0xE9，后两字节为延续字节 (10xxxxxx)。
  for(i=0; i+2<len; i++) {
      b0 = str[i] < 0 ? str[i] + 256 : str[i];
      b1 = str[i+1] < 0 ? str[i+1] + 256 : str[i+1];
      b2 = str[i+2] < 0 ? str[i+2] + 256 : str[i+2];
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
    b = str[i] < 0 ? str[i] + 256 : str[i];
    if ((b & 0xC0) != 0x80) n++;
  }
  return n;
}
