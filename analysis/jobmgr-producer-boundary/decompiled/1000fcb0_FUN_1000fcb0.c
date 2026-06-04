/* Function: 1000fcb0 FUN_1000fcb0 */


undefined4 FUN_1000fcb0(int *param_1)

{
  bool bVar1;
  undefined *puVar2;
  undefined *puVar3;
  undefined4 uVar4;
  undefined4 uVar5;
  int iVar6;
  undefined4 uVar7;
  undefined4 uVar8;

  uVar4 = 0;
  iVar6 = *(int *)PTR_DAT_10006340;
  bVar1 = false;
  if (iVar6 == 1) {
    if ((*param_1 == 0x25) || (*param_1 == 0x11)) {
      if (*(int *)(PTR_DAT_10006340 + 0xc) == 0) {
        if ((*(uint *)(PTR_DAT_10006338 + 0x10) & DAT_10005f74) == DAT_10006370) {
          *(undefined4 *)PTR_DAT_10006340 = 3;
          uVar4 = 7;
          bVar1 = true;
        }
        else {
          *(undefined4 *)PTR_DAT_10006340 = 0;
        }
      }
      else {
        uVar4 = 8;
        *(undefined4 *)PTR_DAT_10006340 = 2;
      }
      goto LAB_1000fda0;
    }
    goto LAB_1000fd9d;
  }
  if (iVar6 == 0) goto LAB_1000fda0;
  if (iVar6 == 2) {
    if (*param_1 == 0xb) {
      iVar6 = param_1[3];
      if (((*(uint *)(PTR_DAT_10006340 + 0x14) == (uint)*(ushort *)(iVar6 + 10)) &&
          (*(uint *)(PTR_DAT_10006340 + 0x18) == (uint)*(ushort *)(iVar6 + 0x10))) &&
         (*(uint *)(PTR_DAT_10006340 + 0x10) == (uint)*(ushort *)(iVar6 + 0xe))) {
        bVar1 = true;
        uVar4 = 7;
        *(undefined4 *)PTR_DAT_10006340 = 3;
      }
      else {
        *(undefined4 *)PTR_DAT_10006340 = 0;
      }
      goto LAB_1000fda0;
    }
    if ((*param_1 == 0x2d) && (param_1[1] == 1)) {
LAB_1000fd54:
      if (*(int *)(PTR_DAT_10006340 + 8) == 0) goto LAB_1000fd95;
    }
LAB_1000fd9d:
    uVar4 = 8;
  }
  else {
    if (iVar6 != 3) goto LAB_1000fda0;
    iVar6 = *param_1;
    if (iVar6 == 0x32) {
      if (param_1[1] == 1) {
        *(undefined4 *)PTR_DAT_10006340 = 0;
        uVar4 = 9;
        uVar5 = 0;
        uVar7 = 0x1a;
        uVar8 = 0;
      }
      else {
        uVar4 = 8;
        *(undefined4 *)PTR_DAT_10006340 = 0;
        uVar5 = 10;
        uVar7 = 0xf;
        uVar8 = 2;
      }
      FUN_10010218(uVar5,uVar7,uVar8,0,0);
      bVar1 = false;
      goto LAB_1000fda0;
    }
    if (iVar6 == 0x2d) goto LAB_1000fd54;
    if (iVar6 != 0x2c) goto LAB_1000fd9d;
LAB_1000fd95:
    *(undefined4 *)PTR_DAT_10006340 = 0;
    uVar4 = 9;
  }
LAB_1000fda0:
  puVar3 = PTR_DAT_10006344;
  puVar2 = PTR_DAT_10006340;
  if (bVar1) {
    uVar5 = *(undefined4 *)(PTR_DAT_10006340 + 0x20);
    *(undefined4 *)(PTR_DAT_10006344 + 0xc) = uVar4;
    *(undefined4 *)(puVar3 + 4) = uVar5;
    uVar5 = *(undefined4 *)(puVar2 + 0x1c);
    *(undefined4 *)puVar3 = *(undefined4 *)(puVar2 + 0x24);
    *(undefined4 *)(puVar3 + 8) = uVar5;
  }
  return uVar4;
}
