/* Function: 10010b0c hp1020_delay_mgr_receive_thread_candidate */


/* WARNING: Control flow encountered bad instruction data */
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void hp1020_delay_mgr_receive_thread_candidate(void)

{
  undefined *puVar1;
  uint uVar2;
  int iVar3;
  uint *puVar4;
  int *piVar5;
  undefined4 *puVar6;
  undefined4 *puVar7;
  uint uVar8;
  uint *puVar9;
  uint uVar10;
  uint uVar11;
  undefined1 auStack_50 [16];
  undefined4 uStack_40;
  undefined4 uStack_3c;
  uint uStack_30;
  uint uStack_2c;

  FUN_1001214c();
  puVar4 = _UNK_10006458;
  uVar2 = FUN_100175cc();
  *puVar4 = uVar2;
  do {
    iVar3 = threadx_queue_receive_wait_candidate(PTR_DAT_10006438,auStack_50,0xffffffff);
    if (iVar3 == 10) {
      uStack_2c = FUN_100175cc();
      uStack_30 = *_UNK_10006458;
      if (uStack_30 < uStack_2c) {
        uStack_30 = uStack_2c - uStack_30;
      }
      else {
        uStack_30 = (uStack_2c - 1) - uStack_30;
      }
      FUN_100181a4(PTR_DAT_10006430,0xffffffff);
      uVar8 = 0;
      uVar2 = uStack_2c;
      if (*(int *)PTR_DAT_10006454 != 0) {
        puVar9 = (uint *)(PTR_DAT_1000645c + 0x10);
        puVar4 = (uint *)(PTR_DAT_1000645c + 4);
        piVar5 = (int *)(PTR_DAT_1000645c + 8);
        puVar7 = (undefined4 *)(PTR_DAT_1000645c + 0xc);
        puVar6 = (undefined4 *)PTR_DAT_1000645c;
        uVar10 = uStack_30;
        do {
          if (uVar10 < *puVar9) {
            uVar11 = *puVar9 - uVar10;
          }
          else {
            uStack_40 = 0x43;
            uStack_3c = *puVar7;
            uStack_30 = uVar10;
            uStack_2c = uVar2;
            hp1020_queue_send_candidate(*puVar6,&uStack_40);
            uVar11 = 0;
            uVar10 = uStack_30;
            uVar2 = uStack_2c;
            if (*piVar5 != 0) {
              uVar11 = *puVar4;
            }
          }
          *puVar9 = uVar11;
          puVar9 = puVar9 + 5;
          puVar4 = puVar4 + 5;
          piVar5 = piVar5 + 5;
          puVar6 = puVar6 + 5;
          puVar7 = puVar7 + 5;
          uVar8 = uVar8 + 1;
        } while (uVar8 < *(uint *)PTR_DAT_10006454);
      }
      puVar1 = PTR_DAT_10006454;
      uVar8 = 0;
      if (*(int *)PTR_DAT_10006454 != 0) {
        piVar5 = (int *)(PTR_DAT_1000645c + 0x10);
        do {
          if (*piVar5 == 0) {
            uVar10 = uVar8;
            if (uVar8 < *(int *)PTR_DAT_10006454 - 1U) {
              do {
                uVar11 = uVar10 + 1;
                uStack_2c = uVar2;
                FUN_1001b38c(PTR_DAT_1000645c + uVar10 * 0x14,PTR_DAT_1000645c + uVar11 * 0x14,0x14)
                ;
                uVar10 = uVar11;
                uVar2 = uStack_2c;
              } while (uVar11 < *(int *)puVar1 - 1U);
            }
            piVar5 = piVar5 + -5;
            uVar8 = uVar8 - 1;
            *(int *)puVar1 = *(int *)puVar1 + -1;
          }
          piVar5 = piVar5 + 5;
          uVar8 = uVar8 + 1;
        } while (uVar8 < *(uint *)PTR_DAT_10006454);
      }
      if (*(int *)PTR_DAT_10006454 != 0) {
                    /* WARNING: Bad instruction - Truncating control flow here */
        halt_baddata();
      }
    }
    else {
      uStack_2c = FUN_100175cc();
      FUN_100181a4(PTR_DAT_10006430,0xffffffff);
      uVar2 = uStack_2c;
      if (*(int *)PTR_DAT_10006454 != 0) {
                    /* WARNING: Bad instruction - Truncating control flow here */
        halt_baddata();
      }
    }
    puVar1 = PTR_DAT_10006430;
    *_UNK_10006458 = uVar2;
    FUN_10018214(puVar1);
  } while( true );
}
