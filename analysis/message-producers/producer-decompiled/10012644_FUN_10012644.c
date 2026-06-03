/* Function: 10012644 FUN_10012644 */


void FUN_10012644(int param_1)

{
  undefined *puVar1;
  int iVar2;
  
  FUN_100181a4(PTR_DAT_10006624 + param_1 * 0x1c,0xffffffff);
  puVar1 = PTR_DAT_100062e4;
  iVar2 = *(int *)PTR_DAT_100062e4;
  while (iVar2 != 0) {
    threadx_sleep_candidate(0x32);
    iVar2 = *(int *)puVar1;
  }
  return;
}


