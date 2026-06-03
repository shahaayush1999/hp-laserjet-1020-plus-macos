/* Function: 10013140 FUN_10013140 */


void FUN_10013140(undefined4 param_1,undefined4 param_2)

{
  uint uVar1;
  undefined *puVar2;
  undefined4 unaff_retaddr;
  int iVar3;
  uint uVar4;
  int *piVar5;
  undefined4 local_30 [12];
  
  memw();
  *(undefined4 *)PTR_DAT_100066b4 = unaff_retaddr;
  do {
    uVar4 = 0;
    do {
      iVar3 = FUN_100131b8(param_1,param_2);
      puVar2 = PTR_DAT_100066b4;
      uVar1 = DAT_10005eb0;
      if (iVar3 != 0) {
        piVar5 = (int *)(iVar3 + -0xc);
        iVar3 = *piVar5;
        while (iVar3 != DAT_100066a4) {
          piVar5 = piVar5 + -1;
          iVar3 = *piVar5;
        }
        uVar4 = piVar5[2] & DAT_100066b8;
        piVar5[2] = uVar4;
        memw();
        piVar5[2] = uVar4 | *(uint *)puVar2 & uVar1;
        return;
      }
      FUN_1001766c(10);
      uVar4 = uVar4 + 1;
    } while (uVar4 < 10);
    local_30[0] = 0x21;
    FUN_10013658(3,local_30);
  } while( true );
}


