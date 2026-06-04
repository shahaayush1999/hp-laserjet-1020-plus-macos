/* Function: 10017ca0 FUN_10017ca0 */


undefined4 FUN_10017ca0(int *param_1,undefined4 param_2)

{
  undefined4 uVar1;
  
  if ((param_1 == (int *)0x0) || (*param_1 == DAT_100065a8)) {
    return 6;
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
  uVar1 = FUN_10019308(param_1,param_2);
  return uVar1;
}


