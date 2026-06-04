/* Function: 1000d2a8 hp1020_pjl_command_dispatch_candidate */


/* low confidence: Caller of PJL echo matcher */

undefined4 hp1020_pjl_command_dispatch_candidate(void)

{
  char cVar1;
  bool bVar2;
  bool bVar3;
  undefined *puVar4;
  undefined *puVar5;
  byte *pbVar6;
  byte *pbVar7;
  int iVar8;
  undefined4 uStack_30;
  
  pbVar6 = *(byte **)(PTR_PTR_10006274 + 0x1c);
  bVar3 = false;
  hp1020_pjl_read_or_poll_candidate();
  bVar2 = true;
  iVar8 = *(int *)PTR_DAT_10006270;
  uStack_30 = 2;
  while ((puVar4 = PTR_DAT_10006270, iVar8 == 0x20 || (iVar8 == 9))) {
    hp1020_pjl_read_or_poll_candidate();
    iVar8 = *(int *)PTR_DAT_10006270;
  }
  if (*(int *)PTR_DAT_10006270 != -1) {
    FUN_1000dd60();
  }
  cVar1 = *PTR_DAT_1000626c;
  do {
    if (cVar1 != '\0') {
      if (bVar3) {
        FUN_1000dd7c(2);
        hp1020_pjl_echo_matcher();
        uStack_30 = 0;
      }
      return uStack_30;
    }
    hp1020_pjl_read_or_poll_candidate();
    puVar5 = PTR_DAT_10006270;
    iVar8 = *(int *)puVar4;
    pbVar7 = pbVar6;
    if (iVar8 != 10) {
      if (((iVar8 < 0x21) && (iVar8 != 0x20)) && (iVar8 != 9)) {
        FUN_1000dd7c(2);
        if (*(int *)puVar4 != -1) {
          FUN_1000dd60();
        }
        return 6;
      }
      if (bVar2) {
        if (*pbVar6 == 0x20) {
          iVar8 = *(int *)puVar4;
          while ((iVar8 == 0x20 || (iVar8 == 9))) {
            hp1020_pjl_read_or_poll_candidate();
            iVar8 = *(int *)puVar5;
          }
          iVar8 = *(int *)puVar4;
LAB_1000d394:
          pbVar7 = pbVar6 + 1;
          if (iVar8 != -1) {
            FUN_1000dd60();
          }
        }
        else {
          if (*(int *)puVar4 - 0x61U < 0x1a) {
            *(int *)puVar4 = *(int *)puVar4 + -0x20;
          }
          if (*(uint *)puVar4 == (uint)*pbVar6) {
            pbVar7 = pbVar6 + 1;
            if (*pbVar7 != 0) goto LAB_1000d39a;
            hp1020_pjl_read_or_poll_candidate();
            iVar8 = *(int *)puVar4;
            if (((iVar8 != 10) && (iVar8 != 0x20)) && (iVar8 != 9)) {
              bVar2 = false;
              goto LAB_1000d394;
            }
            bVar3 = true;
          }
          bVar2 = false;
        }
      }
    }
LAB_1000d39a:
    cVar1 = *PTR_DAT_1000626c;
    pbVar6 = pbVar7;
  } while( true );
}


