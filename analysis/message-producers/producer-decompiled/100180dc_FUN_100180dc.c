/* Function: 100180dc FUN_100180dc */


undefined4 FUN_100180dc(int *param_1,int param_2,int param_3)

{
  undefined4 uVar1;
  
  if ((param_1 == (int *)0x0) || (*param_1 != DAT_100065e8)) {
    return 9;
  }
  if (param_2 == 0) {
    return 3;
  }
  if ((param_3 != 0) &&
     ((*(int *)PTR_DAT_10005d80 != 0 || (*(undefined **)PTR_DAT_10006a9c == PTR_DAT_10006ae8)))) {
    return 4;
  }
  uVar1 = FUN_1001a130(param_1,param_2,param_3);
  return uVar1;
}


