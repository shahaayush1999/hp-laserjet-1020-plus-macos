/*
Function: 1000d6b0 hp1020_pjl_read_or_poll_candidate
Score: 26
*/


void hp1020_pjl_read_or_poll_candidate(void)

{
  undefined *puVar1;
  undefined *puVar2;
  int iVar3;
  
  iVar3 = FUN_1000d674();
  puVar1 = PTR_DAT_10006270;
  *(int *)PTR_DAT_10006270 = iVar3;
  if (iVar3 == 0xd) {
    iVar3 = FUN_1000d674();
    *(int *)puVar1 = iVar3;
    puVar2 = PTR_DAT_10006298;
    if (iVar3 == 10) {
      *PTR_DAT_1000626c = 1;
      *puVar2 = 1;
    }
    else {
      if (iVar3 != -1) {
        FUN_1000dd60();
      }
      *(undefined4 *)puVar1 = 0xd;
    }
  }
  else if (iVar3 == 10) {
    *PTR_DAT_1000626c = 1;
    *PTR_DAT_10006298 = 0;
  }
  return;
}


