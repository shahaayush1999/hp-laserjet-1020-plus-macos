/* Function: 100138fc hp1020_init_timer_candidate */


void hp1020_init_timer_candidate(void)

{
  uint *puVar1;
  uint uVar2;
  uint uVar3;
  uint uVar4;
  
  uVar2 = DAT_100066c4;
  puVar1 = DAT_100064cc;
  uVar3 = DAT_1000628c;
  uVar4 = DAT_10005e34;
  if ((*(uint *)PTR_DAT_1000672c & 1) == 0) {
    memw();
    uVar4 = *DAT_100064cc;
    *PTR_DAT_10006724 = 1;
    memw();
    *puVar1 = uVar4 & uVar3;
    uVar4 = DAT_100066a0;
    memw();
    uVar3 = *puVar1;
    *PTR_DAT_10006728 = 0;
    memw();
    *puVar1 = uVar3 | uVar4;
  }
  else if ((*(uint *)PTR_DAT_1000672c & 1) == 1) {
    memw();
    uVar3 = *DAT_100064cc;
    *PTR_DAT_10006728 = 1;
    memw();
    *puVar1 = uVar3 & uVar2;
    memw();
    uVar3 = *puVar1;
    *PTR_DAT_10006724 = 0;
    memw();
    *puVar1 = uVar3 | uVar4;
  }
  *(int *)PTR_DAT_1000672c = *(int *)PTR_DAT_1000672c + 1;
  return;
}


