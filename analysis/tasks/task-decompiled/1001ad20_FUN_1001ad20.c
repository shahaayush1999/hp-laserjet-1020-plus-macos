/* Function: 1001ad20 FUN_1001ad20 */


undefined4 FUN_1001ad20(void)

{
  undefined *puVar1;
  undefined *puVar2;
  int iVar3;
  int iVar4;
  undefined4 uVar5;
  undefined4 uVar6;
  
  iVar4 = *(int *)PTR_DAT_10006a9c;
  uVar5 = 0;
  uVar6 = rsil(1);
  if (*(int *)(iVar4 + 0x30) == 0) {
    iVar3 = *(int *)PTR_DAT_10006ac0;
    *(undefined4 *)(iVar4 + 0x18) = *(undefined4 *)(iVar4 + 0x1c);
    puVar2 = PTR_DAT_10006ab8;
    puVar1 = PTR_DAT_10006aac;
    if (iVar3 == 0) {
      if ((*(int *)(iVar4 + 0x20) != iVar4) && (*(int *)(iVar4 + 0x2c) == *(int *)(iVar4 + 0x3c))) {
        *(int *)(PTR_DAT_10006ab8 + *(int *)(iVar4 + 0x2c) * 4) = *(int *)(iVar4 + 0x20);
        uVar5 = 1;
        *(undefined4 *)PTR_DAT_10006aa0 = *(undefined4 *)(puVar2 + *(int *)puVar1 * 4);
      }
    }
    else {
      *(undefined4 *)(iVar4 + 0x18) = 1;
    }
  }
  wsr(0,uVar6);
  rsync();
  return uVar5;
}


