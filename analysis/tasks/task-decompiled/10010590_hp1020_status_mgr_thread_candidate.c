/* Function: 10010590 hp1020_status_mgr_thread_candidate */


void hp1020_status_mgr_thread_candidate(void)

{
  undefined *puVar1;
  undefined *puVar2;
  undefined *puVar3;
  undefined *puVar4;
  undefined4 uVar5;
  uint uVar6;
  int iVar7;
  uint uVar8;
  undefined4 uStack_30;
  int iStack_2c;
  undefined4 uStack_28;
  int *piStack_24;
  
  FUN_1001214c();
  FUN_10010838(DAT_100063dc,1);
  puVar4 = PTR_DAT_10006408;
  puVar2 = PTR_DAT_100063d8;
  puVar1 = PTR_DAT_100063b0;
switchD_100105cd_caseD_10:
  FUN_1001809c(PTR_DAT_100063b4,&uStack_30,0xffffffff);
  puVar3 = PTR_DAT_100063e0;
  switch(uStack_30) {
  case 0xf:
    if (puVar2[0x18] == '\0') goto switchD_100105cd_caseD_10;
    iVar7 = FUN_10011178(0x1b);
    uVar5 = DAT_10006410;
    if (iVar7 == 1) {
      uVar5 = DAT_1000640c;
    }
    FUN_10010838(uVar5,10);
    uVar5 = 3;
    break;
  default:
    goto switchD_100105cd_caseD_10;
  case 0x2c:
    FUN_10010838(iStack_2c,uStack_28);
    goto switchD_100105cd_caseD_10;
  case 0x2e:
    iVar7 = *(int *)PTR_DAT_100063e0;
    puVar2[0x18] = puVar2[0x18] + '\x01';
    *(int *)puVar3 = iVar7 + 1;
    iVar7 = FUN_10011178(0x1b);
    if (iVar7 - 1U < 7) {
                    /* WARNING: Could not recover jumptable at 0x10010605. Too many branches */
                    /* WARNING: Treating indirect jump as call */
      (**(code **)(PTR_switchdataD_10004b30_10006404 + (iVar7 - 1U) * 4))();
      return;
    }
    FUN_10010838(DAT_10006400,10);
    if ((piStack_24 != (int *)0x0) && ((piStack_24[0x10] & 0x20000000U) != 0)) {
      FUN_1000b344(piStack_24,uStack_28);
    }
    goto switchD_100105cd_caseD_10;
  case 0x2f:
    if (puVar2[0x18] != '\0') {
      iVar7 = *(int *)puVar4;
      puVar2[0x18] = puVar2[0x18] + -1;
      *(int *)puVar4 = iVar7 + 1;
    }
    iVar7 = *piStack_24;
    if ((iVar7 != 0) && ((*(uint *)(iVar7 + 0x40) & 0x20000000) != 0)) {
      FUN_1000b3f8(iVar7,piStack_24[1],*(undefined2 *)(piStack_24 + 3),
                   *(undefined1 *)((int)piStack_24 + 0xb));
    }
    if (piStack_24[1] != 0) {
      FUN_10013408();
    }
    FUN_10013408(piStack_24);
    if (puVar2[0x18] == '\0') {
      FUN_10010838(DAT_1000604c,10);
    }
    goto switchD_100105cd_caseD_10;
  case 0x30:
    if (puVar2[0x18] != '\0') {
      iVar7 = *(int *)puVar4;
      puVar2[0x18] = puVar2[0x18] + -1;
      *(int *)puVar4 = iVar7 + 1;
    }
    FUN_10010838(DAT_1000604c,10);
    if ((piStack_24 != (int *)0x0) && ((piStack_24[0x10] & 0x20000000U) != 0)) {
      FUN_1000b520(piStack_24,uStack_28,iStack_2c);
    }
    goto switchD_100105cd_caseD_10;
  case 0x31:
    if ((piStack_24 != (int *)0x0) && ((piStack_24[0x10] & 0x10000000U) != 0)) {
      FUN_1000b2a8(piStack_24,iStack_2c);
    }
    goto switchD_100105cd_caseD_10;
  case 0x32:
    if ((((*(uint *)(puVar2 + 8) & DAT_10005c88) == 0) &&
        (uVar6 = *(uint *)(puVar2 + 8) & DAT_10006358, uVar6 != DAT_10006358)) &&
       (uVar6 != DAT_1000635c)) goto switchD_100105cd_caseD_10;
    uVar5 = *(undefined4 *)(puVar2 + 0x14);
    break;
  case 0x43:
    goto switchD_100105cd_caseD_43;
  }
  FUN_10013658(uVar5,&uStack_30);
  goto switchD_100105cd_caseD_10;
switchD_100105cd_caseD_43:
  FUN_10017e64(PTR_DAT_100063d0,0xffffffff);
  uVar6 = 0;
  uVar8 = 0;
  do {
    iVar7 = *(int *)(puVar1 + uVar8 * 4);
    if (((iVar7 != 0) && ((*(uint *)(iVar7 + 0x40) >> 0x13 & 0x1ff) != 0)) && (iVar7 == iStack_2c))
    {
      uVar5 = FUN_10011178(0x19);
      FUN_1000b774(*(int *)(puVar1 + uVar8 * 4),uVar5);
    }
    uVar6 = uVar6 + 1;
    uVar8 = uVar6 & 0xff;
  } while (uVar8 < 0x14);
  FUN_10017ed8(PTR_DAT_100063d0);
  goto switchD_100105cd_caseD_10;
}


