/* Function: 100187e0 FUN_100187e0 */


undefined8 FUN_100187e0(void)

{
  undefined *puVar1;
  int iVar2;
  int *piVar3;
  undefined4 *puVar4;
  undefined4 uVar5;
  int iVar6;
  undefined4 uVar7;
  undefined4 uVar8;
  undefined4 uVar9;
  undefined4 uVar10;
  undefined1 in_LBEG;
  undefined1 in_LEND;
  undefined1 in_LCOUNT;
  undefined1 in_SAR;
  undefined1 in_EPC1;
  uint uVar11;
  
  uVar11 = 0;
  iVar6 = *(int *)PTR_DAT_10006b18;
  wsr(0,*(undefined4 *)(iVar6 + 0x50));
  rsync();
  puVar4 = *(undefined4 **)PTR_PTR_10006b1c;
  *(undefined4 *)(iVar6 + 0x70) = *puVar4;
  *(undefined4 *)(iVar6 + 0x74) = puVar4[1];
  *(undefined4 *)(iVar6 + 0x78) = puVar4[2];
  *(undefined4 *)(iVar6 + 0x7c) = puVar4[3];
  iVar2 = *(int *)PTR_DAT_10005d80;
  *(int *)PTR_DAT_10005d80 = iVar2 + -1;
  if (iVar2 + -1 != 0) {
    breakpoint(0x1000,0x100188e9,1,1);
    do {
                    /* WARNING: Do nothing block with infinite loop */
    } while( true );
  }
  do {
    uVar7 = *(undefined4 *)(iVar6 + 0x10);
    uVar8 = *(undefined4 *)(iVar6 + 0x14);
    uVar9 = *(undefined4 *)(iVar6 + 0x18);
    uVar10 = *(undefined4 *)(iVar6 + 0x1c);
    if (*(undefined1 **)PTR_DAT_10006a9c == (undefined1 *)0x0) {
      if (*(undefined1 **)PTR_DAT_10006aa0 == (undefined1 *)0x0) {
LAB_100188b2:
        iVar2 = *(int *)PTR_DAT_10006b18;
        wsr((char)uVar11,*(undefined4 *)(iVar2 + 0x50));
        rsync();
        wsr(in_EPC1,*(undefined4 *)(iVar2 + 0x54));
        wsr(in_SAR,*(undefined4 *)(iVar2 + 0x4c));
        wsr(in_LBEG,*(undefined4 *)(iVar2 + 0x40));
        wsr(in_LEND,*(undefined4 *)(iVar2 + 0x44));
        wsr(in_LCOUNT,*(undefined4 *)(iVar2 + 0x48));
        rfe();
        return CONCAT44(*(undefined4 *)(iVar2 + 0xc),*(undefined4 *)(iVar2 + 8));
      }
      *(undefined4 *)PTR_DAT_10006b18 = *(undefined4 *)(*(int *)PTR_DAT_10006aa0 + 8);
      piVar3 = (int *)PTR_DAT_10006a9c;
    }
    else {
      if (((*(int *)PTR_DAT_10006ac0 != 0) ||
          (*(undefined1 **)PTR_DAT_10006aa0 == (undefined1 *)0x0)) ||
         (*(undefined1 **)PTR_DAT_10006aa0 == *(undefined1 **)PTR_DAT_10006a9c)) goto LAB_100188b2;
      *(undefined4 *)(*(int *)PTR_DAT_10006a9c + 8) = *(undefined4 *)PTR_DAT_10006b18;
      puVar1 = PTR_DAT_10006b18;
      uVar5 = *(undefined4 *)PTR_DAT_10006b18;
      *(undefined4 *)PTR_DAT_10006b18 = *(undefined4 *)(*(int *)PTR_DAT_10006aa0 + 8);
      uVar11 = uVar11 & 0xffffcfff;
      FUN_1001b128(uVar5,puVar1,uVar7,uVar8,uVar9,uVar10);
      puVar1 = PTR_DAT_10006ac8;
      piVar3 = (int *)PTR_DAT_10006a9c;
      if (*(int *)PTR_DAT_10006ac8 != 0) {
        *(int *)(*(int *)PTR_DAT_10006a9c + 0x18) = *(int *)PTR_DAT_10006ac8;
        *(undefined4 *)puVar1 = 0;
      }
    }
    iVar2 = *(int *)PTR_DAT_10006aa0;
    *piVar3 = iVar2;
    *(int *)(iVar2 + 4) = *(int *)(iVar2 + 4) + 1;
    *(undefined4 *)PTR_DAT_10006ac8 = *(undefined4 *)(iVar2 + 0x18);
    iVar6 = *(int *)PTR_DAT_10006b18;
  } while( true );
}


