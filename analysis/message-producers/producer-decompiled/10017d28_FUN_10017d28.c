/* Function: 10017d28 FUN_10017d28 */


undefined4 FUN_10017d28(int *param_1,undefined4 param_2,uint param_3,int param_4,int param_5)

{
  undefined4 uVar1;
  
  if ((param_1 == (int *)0x0) || (*param_1 != DAT_100065a8)) {
    return 6;
  }
  if (param_4 == 0) {
    return 3;
  }
  if ((param_5 != 0) &&
     ((*(int *)PTR_DAT_10005d80 != 0 || (*(undefined **)PTR_DAT_10006a9c == PTR_DAT_10006ae8)))) {
    return 4;
  }
  if (3 < param_3) {
    return 8;
  }
  uVar1 = FUN_10019408(param_1,param_2,param_3,param_4,param_5);
  return uVar1;
}


