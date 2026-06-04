/* Function: 100199a4 threadx_queue_create_core_candidate */


undefined4
threadx_queue_create_core_candidate
          (undefined4 *param_1,undefined4 param_2,int param_3,int param_4,uint param_5)

{
  undefined *puVar1;
  uint uVar2;
  int iVar3;
  int iVar4;
  undefined4 uVar5;
  
  param_1[1] = param_2;
  param_1[10] = 0;
  param_1[0xb] = 0;
  param_1[2] = param_3;
  if (param_3 == 1) {
    param_5 = param_5 >> 2;
    uVar2 = param_5;
  }
  else if (param_3 == 2) {
    param_5 = param_5 >> 3;
    uVar2 = param_5 << 1;
  }
  else if (param_3 == 4) {
    param_5 = param_5 >> 4;
    uVar2 = param_5 << 2;
  }
  else if (param_3 == 8) {
    param_5 = param_5 >> 5;
    uVar2 = param_5 << 3;
  }
  else {
    param_5 = param_5 >> 6;
    uVar2 = param_5 << 4;
  }
  param_1[6] = param_4;
  param_1[7] = uVar2 * 4 + param_4;
  param_1[8] = param_4;
  param_1[9] = param_4;
  param_1[4] = 0;
  param_1[5] = param_5;
  param_1[3] = param_5;
  puVar1 = PTR_DAT_10006b70;
  uVar5 = rsil(1);
  iVar4 = *(int *)PTR_DAT_10006b70;
  *param_1 = DAT_100065e8;
  if (iVar4 == 0) {
    *(undefined4 **)puVar1 = param_1;
    param_1[0xc] = param_1;
    param_1[0xd] = param_1;
  }
  else {
    iVar3 = *(int *)(iVar4 + 0x34);
    *(undefined4 **)(iVar4 + 0x34) = param_1;
    *(undefined4 **)(iVar3 + 0x30) = param_1;
    param_1[0xd] = iVar3;
    param_1[0xc] = iVar4;
  }
  *(int *)PTR_DAT_10006b74 = *(int *)PTR_DAT_10006b74 + 1;
  wsr(0,uVar5);
  rsync();
  return 0;
}


