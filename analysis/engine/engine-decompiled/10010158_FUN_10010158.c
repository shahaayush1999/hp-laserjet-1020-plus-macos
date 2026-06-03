/* Function: 10010158 FUN_10010158 */


void FUN_10010158(void)

{
  undefined *puVar1;
  
  puVar1 = PTR_DAT_10006344;
  if (*(int *)(PTR_DAT_10006344 + 0xc) != 0) {
    *(undefined4 *)(PTR_DAT_10006344 + 0xc) = 0;
    *(undefined4 *)(puVar1 + 8) = 4;
    *(undefined4 *)(puVar1 + 4) = 0;
    *(undefined4 *)puVar1 = 0;
  }
  return;
}


