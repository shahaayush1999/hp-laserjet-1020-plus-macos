/* Function: 1001079c FUN_1001079c */


void FUN_1001079c(int param_1)

{
  uint uVar1;
  byte bVar3;
  uint uVar2;
  
  FUN_10017e64(PTR_DAT_100063d0,0xffffffff);
  bVar3 = 0;
  uVar1 = 0;
  do {
    if (*(int *)(PTR_DAT_100063b0 + uVar1 * 4) == param_1) break;
    bVar3 = bVar3 + 1;
    uVar1 = (uint)bVar3;
  } while (uVar1 < 0x14);
  if (bVar3 == 0x14) {
    uVar2 = 0;
    uVar1 = 0;
    do {
      if (*(int *)(PTR_DAT_100063b0 + uVar1 * 4) == 0) {
        *(int *)(PTR_DAT_100063b0 + uVar1 * 4) = param_1;
        break;
      }
      uVar2 = uVar2 + 1;
      uVar1 = uVar2 & 0xff;
    } while (uVar1 < 0x14);
  }
  FUN_10017ed8(PTR_DAT_100063d0);
  return;
}


