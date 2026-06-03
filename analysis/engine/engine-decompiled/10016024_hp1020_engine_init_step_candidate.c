/* Function: 10016024 hp1020_engine_init_step_candidate */


void hp1020_engine_init_step_candidate(void)

{
  undefined *puVar1;
  uint *puVar2;
  uint uVar3;
  undefined4 uVar4;
  
  uVar3 = FUN_10015c68(0x92);
  puVar2 = DAT_10006928;
  puVar1 = PTR_LAB_10006374;
  if ((uVar3 & DAT_10006984) == DAT_10006988) {
    memw();
    uVar3 = *DAT_10006928;
    *(undefined4 *)PTR_DAT_100067c8 = 1;
    memw();
    *puVar2 = uVar3 | (uint)puVar1;
  }
  else {
    if ((uVar3 & DAT_10006984) == DAT_1000698c) {
      uVar4 = 0;
    }
    else if ((uVar3 & DAT_10006984) == DAT_10006990) {
      uVar4 = 0;
    }
    else {
      uVar4 = 2;
    }
    *(undefined4 *)PTR_DAT_100067c8 = uVar4;
  }
  return;
}


