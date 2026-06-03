/* Function: 1000f128 FUN_1000f128 */


void FUN_1000f128(int param_1)

{
  undefined2 uVar1;
  
  *(short *)(param_1 + 0x4e) = *(short *)(param_1 + 0x4e) + -1;
  if (*(short *)(param_1 + 0x72) == 1) {
    uVar1 = 1;
  }
  else {
    if (*(char *)(param_1 + 0x75) == '\x01') {
      FUN_1000f0a8(param_1 + 0x50,2);
      *(short *)(param_1 + 0x4e) = *(short *)(param_1 + 0x4e) + -1;
    }
    uVar1 = 0;
  }
  FUN_1000f0a8(param_1 + 0x50,uVar1);
  return;
}


