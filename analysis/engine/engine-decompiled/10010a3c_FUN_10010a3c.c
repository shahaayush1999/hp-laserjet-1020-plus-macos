/* Function: 10010a3c FUN_10010a3c */


void FUN_10010a3c(undefined4 param_1)

{
  undefined *puVar1;
  uint uVar2;
  int iVar3;
  uint uVar4;
  
  FUN_10017e64(PTR_DAT_100063d0,0xffffffff);
  puVar1 = PTR_DAT_100063b0;
  uVar2 = 0;
  uVar4 = 0;
  do {
    iVar3 = *(int *)(puVar1 + uVar4 * 4);
    if ((iVar3 != 0) && (*(uint *)(iVar3 + 0x40) >> 0x1e != 0)) {
      threadx_sleep_candidate(3);
      FUN_1000b6d8(*(int *)(puVar1 + uVar4 * 4),param_1);
    }
    uVar2 = uVar2 + 1;
    uVar4 = uVar2 & 0xff;
  } while (uVar4 < 0x14);
  FUN_10017ed8(PTR_DAT_100063d0);
  return;
}


