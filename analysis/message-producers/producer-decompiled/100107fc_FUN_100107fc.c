/* Function: 100107fc FUN_100107fc */


void FUN_100107fc(int param_1)

{
  undefined *puVar1;
  uint uVar2;
  uint uVar3;
  
  FUN_10017e64(PTR_DAT_100063d0,0xffffffff);
  puVar1 = PTR_DAT_100063b0;
  uVar3 = 0;
  uVar2 = 0;
  do {
    if (*(int *)(puVar1 + uVar2 * 4) == param_1) {
      *(int *)(puVar1 + uVar2 * 4) = 0;
    }
    uVar3 = uVar3 + 1;
    uVar2 = uVar3 & 0xff;
  } while (uVar2 < 0x14);
  FUN_10017ed8(PTR_DAT_100063d0);
  return;
}


