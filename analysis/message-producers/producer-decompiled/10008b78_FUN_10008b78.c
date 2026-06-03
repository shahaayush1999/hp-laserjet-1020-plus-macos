/* Function: 10008b78 FUN_10008b78 */


void FUN_10008b78(void)

{
  undefined *puVar1;
  int iVar2;
  
  puVar1 = PTR_DAT_10005e10;
  while ((iVar2 = FUN_100130bc(puVar1), iVar2 != 0 && (*(int *)(*(int *)(iVar2 + 0xc) + 0xc) != 0)))
  {
    FUN_10013408(*(undefined4 *)(*(int *)(iVar2 + 0xc) + 4));
    FUN_10013050(puVar1);
    FUN_10013408();
  }
  return;
}


