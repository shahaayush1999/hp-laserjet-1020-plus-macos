/* Function: 10017f90 threadx_queue_delete_candidate */


undefined4 threadx_queue_delete_candidate(int *param_1)

{
  undefined4 uVar1;
  
  if ((param_1 == (int *)0x0) || (*param_1 != DAT_100065e8)) {
    return 9;
  }
  if ((*(undefined **)PTR_DAT_10006a9c != (undefined *)0x0) &&
     ((*(int *)PTR_DAT_10005d80 == 0 && (*(undefined **)PTR_DAT_10006a9c != PTR_DAT_10006ae8)))) {
    uVar1 = threadx_queue_delete_core_candidate(param_1);
    return uVar1;
  }
  return 0x13;
}


