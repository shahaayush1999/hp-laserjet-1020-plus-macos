/* Function: 100165a4 hp1020_engine_register_handlers_candidate */


/* medium confidence: Registers engine event handlers */

void hp1020_engine_register_handlers_candidate(void)

{
  undefined4 *puVar1;
  undefined4 *puVar2;
  undefined4 *puVar3;
  undefined4 *puVar4;
  undefined4 *puVar5;
  undefined4 *puVar6;
  undefined4 *puVar7;
  undefined4 *puVar8;
  undefined4 *puVar9;
  undefined4 *puVar10;
  undefined4 *puVar11;
  undefined4 *puVar12;
  undefined4 local_100;
  undefined4 uStack_fc;
  undefined4 uStack_f8;
  undefined1 uStack_f4;
  undefined4 uStack_d4;
  undefined4 uStack_d0;
  undefined4 uStack_cc;
  undefined4 uStack_c8;
  undefined4 uStack_c4;
  undefined4 uStack_c0;
  undefined4 local_bc;
  undefined4 local_b8;
  undefined4 local_b4;
  undefined4 local_b0;
  undefined4 local_ac;
  undefined4 local_a8;
  undefined4 local_a4;
  undefined4 local_a0;
  undefined4 local_9c;
  undefined4 local_98;
  undefined4 local_94;
  undefined4 local_90;
  undefined4 local_8c;
  undefined4 local_88 [9];
  undefined4 uStack_64;
  undefined4 uStack_60;
  undefined4 uStack_5c;
  undefined4 uStack_50;
  undefined1 *puStack_4c;
  int iStack_40;
  undefined4 *puStack_3c;
  undefined4 *puStack_30;
  
  puStack_4c = (undefined1 *)&local_100;
  uStack_50 = 0x1d;
  hp1020_datastore_read_locked_candidate(&uStack_50);
  local_100 = 4;
  uStack_fc = 0;
  uStack_f4 = 100;
  uStack_f8 = 0;
  uStack_c8 = 1;
  uStack_d4 = 4;
  uStack_cc = 1;
  uStack_d0 = 2;
  iStack_40 = 0;
  puVar9 = &local_94;
  puStack_3c = local_88;
  puStack_30 = &local_8c;
  puVar8 = &local_90;
  puVar1 = &local_98;
  puVar2 = &local_9c;
  puVar3 = &local_a0;
  puVar4 = &local_a4;
  puVar5 = &local_a8;
  puVar7 = &local_ac;
  puVar6 = &local_b0;
  puVar12 = &local_b4;
  puVar11 = &local_b8;
  puVar10 = &local_bc;
  do {
    *puVar10 = 1;
    *puVar11 = 5;
    *puVar12 = 7;
    *puVar6 = 9;
    *puVar7 = 0xb;
    *puVar5 = 0xd;
    *puVar4 = 0x14;
    *puVar3 = 0x1b;
    *puVar2 = 0x22;
    *puVar1 = 0x25;
    *puVar9 = 0x5d;
    *puVar8 = 0x22;
    puVar1 = puVar1 + 0x1c;
    puVar2 = puVar2 + 0x1c;
    puVar3 = puVar3 + 0x1c;
    puVar4 = puVar4 + 0x1c;
    puVar5 = puVar5 + 0x1c;
    puVar7 = puVar7 + 0x1c;
    puVar6 = puVar6 + 0x1c;
    puVar12 = puVar12 + 0x1c;
    puVar11 = puVar11 + 0x1c;
    *puStack_30 = 0x2b;
    *puStack_3c = 0x45;
    *puVar9 = 0;
    *puVar8 = 1;
    puVar10 = puVar10 + 0x1c;
    puStack_3c = puStack_3c + 0x1c;
    puVar9 = puVar9 + 0x1c;
    puStack_30 = puStack_30 + 0x1c;
    puVar8 = puVar8 + 0x1c;
    iStack_40 = iStack_40 + 1;
  } while (iStack_40 == 0);
  uStack_c4 = 0xe;
  uStack_c0 = 2;
  uStack_5c = 1;
  uStack_64 = 1;
  uStack_60 = 0;
  hp1020_datastore_write_notify_unlock_candidate(&uStack_50);
  return;
}


