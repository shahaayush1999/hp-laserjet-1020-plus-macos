/* Function: 1000afec FUN_1000afec */


void FUN_1000afec(undefined4 param_1,uint param_2)

{
  undefined *puVar1;
  uint uVar2;
  int iVar3;
  uint uVar4;
  
  puVar1 = PTR_DAT_100060bc;
  switch(param_1) {
  case 0:
    iVar3 = *(int *)PTR_DAT_100060bc;
    uVar2 = (param_2 & 1) << 0x1d;
    uVar4 = DAT_100060c0;
    goto LAB_1000b079;
  case 1:
    iVar3 = *(int *)PTR_DAT_100060bc;
    uVar2 = (param_2 & 1) << 0x1c;
    uVar4 = DAT_100060c8;
LAB_1000b079:
    *(uint *)(iVar3 + 0x40) = *(uint *)(iVar3 + 0x40) & uVar4 | uVar2;
    *(uint *)(iVar3 + 0x44) = *(uint *)(iVar3 + 0x44) & uVar4 | uVar2;
    break;
  case 2:
    if (param_2 == 0) {
      if ((*(uint *)(*(int *)PTR_DAT_100060bc + 0x40) >> 0x1e != 0) &&
         ((*(uint *)(*(int *)PTR_DAT_100060bc + 0x40) >> 0x13 & 0x1ff) == 0)) {
        FUN_100107fc();
      }
      *(uint *)(*(int *)PTR_DAT_100060bc + 0x40) =
           *(uint *)(*(int *)PTR_DAT_100060bc + 0x40) & DAT_100060c4;
    }
    else {
      iVar3 = *(int *)PTR_DAT_100060bc;
      *(uint *)(iVar3 + 0x40) = *(uint *)(iVar3 + 0x40) & DAT_100060c4 | param_2 << 0x1e;
      FUN_1001079c(iVar3);
    }
    break;
  case 3:
    if (param_2 == 0) {
      if (((*(uint *)(*(int *)PTR_DAT_100060bc + 0x40) >> 0x13 & 0x1ff) != 0) &&
         (FUN_10010cf0(10), *(uint *)(*(int *)puVar1 + 0x40) >> 0x1e == 0)) {
        FUN_100107fc();
      }
      *(uint *)(*(int *)PTR_DAT_100060bc + 0x40) =
           *(uint *)(*(int *)PTR_DAT_100060bc + 0x40) & DAT_100060cc;
    }
    else {
      if ((*(uint *)(*(int *)PTR_DAT_100060bc + 0x40) >> 0x13 & 0x1ff) != 0) {
        FUN_10010cf0(10);
      }
      iVar3 = *(int *)puVar1;
      *(uint *)(iVar3 + 0x40) = *(uint *)(iVar3 + 0x40) & DAT_100060cc | (param_2 & 0x1ff) << 0x13;
      FUN_1001079c(iVar3);
      FUN_10010c98(10,param_2 * 100,1,*(undefined4 *)puVar1);
    }
  }
  return;
}


