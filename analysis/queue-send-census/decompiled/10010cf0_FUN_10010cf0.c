/* Function: 10010cf0 FUN_10010cf0 */


void FUN_10010cf0(int param_1,int param_2)

{
  int iVar1;
  undefined *puVar2;
  undefined *puVar3;
  uint uVar4;
  undefined4 local_40;
  undefined4 uStack_3c;
  int iStack_30;

  iStack_30 = param_1;
  threadx_memory_or_copy_candidate(PTR_DAT_10006430,0xffffffff);
  puVar3 = PTR_DAT_1000645c;
  puVar2 = PTR_DAT_10006454;
  uVar4 = 0;
  if (*(int *)PTR_DAT_10006454 != 0) {
    do {
      if ((*(int *)(puVar3 + uVar4 * 0x14) == iStack_30) &&
         (*(int *)((int)(puVar3 + uVar4 * 0x14) + 0xc) == param_2)) {
        if (uVar4 < *(int *)PTR_DAT_10006454 - 1U) {
          do {
            iVar1 = uVar4 * 0x14;
            uVar4 = uVar4 + 1;
            FUN_1001b38c(puVar3 + iVar1,puVar3 + uVar4 * 0x14,0x14);
          } while (uVar4 < *(int *)puVar2 - 1U);
        }
        local_40 = 0x44;
        uStack_3c = 1;
        *(int *)puVar2 = *(int *)puVar2 + -1;
        hp1020_queue_send_candidate(0xf,&local_40);
      }
      uVar4 = uVar4 + 1;
    } while (uVar4 < *(uint *)PTR_DAT_10006454);
  }
  FUN_10018214(PTR_DAT_10006430);
  return;
}
