/* Function: 10010298 FUN_10010298 */


void FUN_10010298(int param_1,int param_2,undefined4 param_3,undefined4 param_4,undefined4 param_5)

{
  bool bVar1;
  undefined *puVar2;
  int *piVar3;
  int iVar4;
  
  if (param_1 == 0) {
    bVar1 = true;
    param_5 = 0;
  }
  else {
    piVar3 = (int *)FUN_100130bc(PTR_DAT_10006324);
    bVar1 = false;
    if (piVar3 != (int *)0x0) {
      do {
        if (piVar3[3] == param_2) {
          if (piVar3[2] == 0) {
            piVar3[2] = 1;
          }
          else {
            piVar3 = (int *)0x0;
          }
          break;
        }
        piVar3 = (int *)*piVar3;
      } while (piVar3 != (int *)0x0);
      if (piVar3 != (int *)0x0) goto LAB_100102d8;
    }
    param_5 = 1;
    bVar1 = true;
  }
LAB_100102d8:
  if (bVar1) {
    while (iVar4 = FUN_100131b8(0x10,1), iVar4 == 0) {
      threadx_sleep_candidate(0x14);
    }
    *(undefined4 *)(iVar4 + 4) = 0;
    *(undefined4 *)(iVar4 + 8) = param_5;
    puVar2 = PTR_DAT_10006324;
    *(int *)(iVar4 + 0xc) = param_2;
    FUN_10013000(puVar2);
  }
  return;
}


