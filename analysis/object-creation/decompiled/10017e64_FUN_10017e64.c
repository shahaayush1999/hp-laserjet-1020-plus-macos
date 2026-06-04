/* Function: 10017e64 FUN_10017e64 */


undefined4 FUN_10017e64(int *param_1,int param_2)

{
  undefined4 uVar1;
  
  if ((param_1 == (int *)0x0) || (*param_1 != DAT_100065d0)) {
    return 0x1c;
  }
  if ((param_2 != 0) &&
     ((*(int *)PTR_DAT_10005d80 != 0 || (*(undefined **)PTR_DAT_10006a9c == PTR_DAT_10006ae8)))) {
    return 4;
  }
  uVar1 = FUN_10019634(param_1,param_2);
  return uVar1;
}


