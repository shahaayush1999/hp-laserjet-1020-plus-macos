/* Function: 10014244 FUN_10014244 */


void FUN_10014244(void)

{
  undefined *puVar1;
  int *piVar2;
  uint uVar3;
  int iVar4;
  int iVar5;
  int *piVar6;
  undefined4 uVar7;
  
  puVar1 = PTR_DAT_10006770;
  piVar6 = (int *)(PTR_DAT_100067bc + *(int *)(PTR_DAT_10006770 + 0xe0) * 0xc);
  uVar7 = *(undefined4 *)(PTR_DAT_10006770 + *(int *)(PTR_DAT_10006770 + 0xe0) * 4);
  if ((*piVar6 == 0) && (uVar3 = *(uint *)(PTR_DAT_10006770 + 0xd0), uVar3 != 0)) {
    if (*(uint *)(PTR_DAT_10006770 + 0xcc) < uVar3) {
      uVar3 = *(uint *)(PTR_DAT_10006770 + 0xcc);
    }
    piVar6[2] = uVar3;
    piVar2 = DAT_100067e8;
    iVar4 = *(int *)(puVar1 + 0xd0);
    *(uint *)(puVar1 + 0xd0) = iVar4 - uVar3;
    piVar6[1] = (uint)(iVar4 - uVar3 == 0);
    *piVar6 = 1;
    iVar4 = piVar6[2];
    iVar5 = *(int *)(puVar1 + 0xb8);
    memw();
    *DAT_100067e4 = uVar7;
    memw();
    *piVar2 = iVar4 * iVar5;
  }
  return;
}


