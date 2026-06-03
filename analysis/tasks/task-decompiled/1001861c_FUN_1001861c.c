/* Function: 1001861c FUN_1001861c */


void FUN_1001861c(void)

{
  undefined *puVar1;
  undefined4 *puVar2;
  int iVar3;
  undefined1 in_LBEG;
  undefined1 in_LEND;
  undefined1 in_LCOUNT;
  undefined1 in_SAR;
  undefined1 in_EPC1;
  undefined1 in_EXCSAVE1;
  undefined4 local_10;
  undefined4 uStack_c;
  undefined4 uStack_8;
  undefined4 uStack_4;
  
  rsr(in_EXCSAVE1);
  rsr(in_LBEG);
  rsr(in_LEND);
  rsr(in_LCOUNT);
  rsr(in_SAR);
  rsr(0);
  rsr(in_EPC1);
  wsr(in_LCOUNT,0);
  isync();
  *(undefined1 **)PTR_DAT_10006b18 = &stack0xffffff80;
  puVar2 = *(undefined4 **)PTR_PTR_10006b1c;
  *puVar2 = local_10;
  puVar2[1] = uStack_c;
  puVar2[2] = uStack_8;
  puVar2[3] = uStack_4;
  puVar1 = PTR_DAT_10005d80;
  iVar3 = *(int *)PTR_DAT_10005d80;
  *(int *)PTR_DAT_10005d80 = iVar3 + 1;
  if (iVar3 + 1 == 1) {
    (*DAT_10006b20)(puVar1,DAT_10006b20);
    return;
  }
  breakpoint(0x1000,0x100186a1,1,1);
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}


