/* Function: 10013d4c FUN_10013d4c */


/* WARNING: Control flow encountered bad instruction data */

void FUN_10013d4c(undefined4 param_1)

{
  undefined *puVar1;
  undefined *puVar2;
  uint *puVar3;
  uint *puVar4;
  uint uVar5;
  int iVar6;
  undefined8 uVar7;
  undefined4 local_30;
  undefined4 uStack_2c;
  undefined4 uStack_28;
  int iStack_24;
  
  FUN_100171b0(0x13);
  FUN_100171b0(0x14);
  FUN_100171b0(0x15);
  puVar3 = DAT_10006794;
  memw();
  memw();
  *DAT_10006790 = *DAT_10006790 & 0xfffffffe;
  puVar4 = DAT_10006798;
  memw();
  memw();
  *puVar3 = *puVar3 | 2;
  memw();
  memw();
  *puVar4 = *puVar4 | 2;
  memw();
  memw();
  *puVar3 = *puVar3 & 0xfffffffd;
  puVar3 = DAT_1000679c;
  memw();
  memw();
  *puVar4 = *puVar4 & 0xfffffffd;
  uVar5 = DAT_1000628c;
  memw();
  memw();
  *puVar3 = *puVar3 & DAT_1000628c;
  puVar3 = DAT_100067a0;
  memw();
  uStack_28 = 0;
  memw();
  *DAT_100067a0 = *DAT_100067a0 & uVar5;
  puVar2 = PTR_DAT_10006770;
  memw();
  uVar5 = *puVar3;
  iStack_24 = 0;
  while ((uVar5 & 1) != 0) {
    memw();
    uVar5 = *puVar3;
  }
  do {
    memw();
  } while ((*DAT_1000679c & 1) != 0);
  uVar7 = CONCAT44(PTR_DAT_10006770,-(*(int *)(PTR_DAT_10006770 + 0xfc) >> 0x1f));
  if (-(*(int *)(PTR_DAT_10006770 + 0xfc) >> 0x1f) == 0) {
                    /* WARNING: Bad instruction - Truncating control flow here */
    halt_baddata();
  }
  iVar6 = *(int *)(PTR_DAT_10006770 + 0xa0);
  puVar1 = PTR_DAT_10006770;
  while (PTR_DAT_10006770 = puVar1, iVar6 != 0) {
    iVar6 = *(int *)(*(int *)(puVar2 + 0xa0) + 0xc);
    if (*(short *)(iVar6 + 0x4e) != 0) {
      if (*(int *)(iVar6 + 0x54) != 0) {
        *(int *)(iVar6 + 0x54) = *(int *)(iVar6 + 0x54) + -0x10;
      }
      puVar1 = PTR_DAT_100062dc;
      *(short *)(iVar6 + 0x4e) = *(short *)(iVar6 + 0x4e) + -1;
      uVar7 = FUN_10017dac(puVar1,8,0);
    }
    iVar6 = **(int **)(puVar2 + 0xa0);
    *(int *)(puVar2 + 0xa0) = iVar6;
    puVar1 = PTR_DAT_10006770;
  }
  switch(param_1) {
  case 0:
    local_30 = 0x11;
    iStack_24 = FUN_1001608c((int)uVar7,(int)((ulonglong)uVar7 >> 0x20));
    FUN_10013620(0,&local_30);
    puVar2 = PTR_DAT_10006770;
    iStack_24 = *(int *)(PTR_DAT_10006770 + 100);
    *(undefined4 *)(PTR_DAT_10006770 + 0x60) = 0;
    if (iStack_24 != 0) {
      local_30 = 0xb;
      FUN_10013620(8,&local_30);
      *(undefined4 *)(puVar2 + 100) = 0;
    }
    goto switchD_10013e8d_default;
  case 1:
    local_30 = 0x25;
    *(undefined4 *)(puVar1 + 0x60) = 0;
    *(undefined4 *)(puVar1 + 100) = 0;
    goto LAB_10013f21;
  case 2:
  case 7:
    uStack_2c = DAT_100067b4;
    break;
  case 3:
    uStack_2c = DAT_100067a4;
    break;
  case 4:
    uStack_2c = DAT_100067a8;
    break;
  case 5:
    uStack_2c = DAT_100067ac;
    break;
  case 6:
    uStack_2c = DAT_100067b0;
    break;
  default:
    goto switchD_10013e8d_default;
  }
  local_30 = 0x17;
LAB_10013f21:
  FUN_10013620(1,&local_30);
switchD_10013e8d_default:
  puVar2 = PTR_DAT_10006770;
  *(undefined4 *)(PTR_DAT_10006770 + 0x68) = 0;
  *(undefined4 *)(puVar2 + 0x6c) = 0;
  return;
}


