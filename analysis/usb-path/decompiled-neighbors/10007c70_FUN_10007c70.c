/*
Function: 10007c70 FUN_10007c70
Score: 2
*/


void FUN_10007c70(uint param_1)

{
  int iVar1;
  
  iVar1 = 0;
  for (; param_1 != 0; param_1 = param_1 >> 1) {
    iVar1 = iVar1 + 1;
  }
  *(undefined4 *)((iVar1 + -1) * 0x58 + DAT_10005da8) = 0;
  return;
}


