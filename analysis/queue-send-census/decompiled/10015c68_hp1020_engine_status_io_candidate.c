/* Function: 10015c68 hp1020_engine_status_io_candidate */


uint hp1020_engine_status_io_candidate(undefined2 param_1)

{
  uint uVar1;
  uint uVar2;
  uint *puVar3;
  undefined *puVar4;
  uint uVar5;
  uint *puVar6;
  int iVar7;
  int iVar8;
  undefined1 auStack_40 [16];
  undefined4 uStack_30;
  undefined4 uStack_2c;
  int iStack_28;
  int iStack_24;

  puVar6 = DAT_10006928;
  uVar5 = DAT_10006924;
  puVar4 = PTR_DAT_10006920;
  puVar3 = DAT_1000691c;
  uVar2 = DAT_10005f20;
  uVar1 = DAT_10005d04;
  iVar8 = 4;
  *(undefined2 *)(PTR_DAT_10006920 + 0x5a) = param_1;
  memw();
  memw();
  *puVar3 = *puVar3 & uVar5;
  do {
    memw();
    if ((*DAT_1000691c & uVar2) == 0) {
      FUN_1001766c(1);
    }
    else {
      memw();
      memw();
      *puVar6 = *puVar6 & uVar1 | (uint)*(ushort *)(puVar4 + 0x5a);
      memw();
      memw();
      *puVar6 = *puVar6 | uVar2;
      FUN_10017184(6);
      iVar7 = FUN_10017d28(puVar4,1,3,auStack_40,200);
      if (iVar7 == 0) {
        *(undefined2 *)(puVar4 + 0x5a) = 0;
        break;
      }
    }
    iVar8 = iVar8 + -1;
  } while (iVar8 != 0);
  if (iVar8 == 0) {
    uStack_30 = 0x17;
    uStack_2c = DAT_1000692c;
    iStack_28 = iVar8;
    iStack_24 = iVar8;
    hp1020_queue_send_candidate(1,&uStack_30);
    return DAT_100068e4;
  }
  return (uint)*(ushort *)(PTR_DAT_10006920 + 0x5c);
}
