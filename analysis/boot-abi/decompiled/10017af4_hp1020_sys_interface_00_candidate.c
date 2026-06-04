/* Function: 10017af4 hp1020_sys_interface_00_candidate */


undefined4
hp1020_sys_interface_00_candidate(int *param_1,int param_2,undefined4 param_3,int param_4)

{
  undefined4 uVar1;
  
  if ((param_1 == (int *)0x0) || (*param_1 != DAT_10006b10)) {
    return 2;
  }
  if (param_2 == 0) {
    return 3;
  }
  if ((param_4 != 0) &&
     ((*(int *)PTR_DAT_10005d80 != 0 || (*(undefined **)PTR_DAT_10006a9c == PTR_DAT_10006ae8)))) {
    return 4;
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
  uVar1 = FUN_10018eac(param_1,param_2,param_3,param_4);
  return uVar1;
}


