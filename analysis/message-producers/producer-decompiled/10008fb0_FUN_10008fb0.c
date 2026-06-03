/* Function: 10008fb0 FUN_10008fb0 */


void FUN_10008fb0(void)

{
  undefined *puVar1;
  int iVar2;
  
  FUN_100171b0(4);
  puVar1 = PTR_DAT_10005e10;
  while (iVar2 = FUN_100130bc(puVar1), iVar2 != 0) {
    FUN_10013408(*(undefined4 *)(*(int *)(iVar2 + 0xc) + 4));
    FUN_10013050(puVar1);
    FUN_10013408();
  }
  FUN_10017184(4);
  return;
}


