/* Function: 10017f18 threadx_queue_create_candidate */


undefined4
threadx_queue_create_candidate
          (int *param_1,undefined4 param_2,uint param_3,int param_4,uint param_5)

{
  undefined4 uVar1;
  
  if ((param_1 == (int *)0x0) || (*param_1 == DAT_100065e8)) {
    return 9;
  }
  if (param_4 == 0) {
    return 3;
  }
  if ((((1 < param_3 - 1) && (param_3 != 4)) && (param_3 != 8)) && (param_3 != 0x10)) {
    return 5;
  }
  if (param_5 >> 2 < param_3) {
    return 5;
  }
  if (*(int *)PTR_DAT_10006a9c == 0) {
    if (*(int *)PTR_DAT_10005d80 != DAT_10006a94) {
      return 0x13;
    }
  }
  else if (*(int *)PTR_DAT_10005d80 != 0) {
    return 0x13;
  }
  if (*(undefined **)PTR_DAT_10006a9c == PTR_DAT_10006ae8) {
    return 0x13;
  }
  uVar1 = threadx_queue_create_core_candidate(param_1,param_2,param_3,param_4,param_5);
  return uVar1;
}


