/* Function: 1000f228 FUN_1000f228 */


void FUN_1000f228(void)

{
  int iVar1;
  
  iVar1 = FUN_10013140(0x94,1);
  FUN_100130c4(iVar1 + 0x58);
  FUN_100130c4(iVar1 + 0x50);
  FUN_100130c4(iVar1 + 0x60);
  FUN_100130c4(iVar1 + 0x68);
  *(undefined2 *)(iVar1 + 0x70) = 0;
  *(undefined4 *)(iVar1 + 0x84) = 0;
  *(undefined4 *)(iVar1 + 0x88) = 0;
  *(undefined4 *)(iVar1 + 0x8c) = 0;
  *(undefined1 *)(iVar1 + 0x90) = 0;
  *(undefined1 *)(iVar1 + 0x74) = 0;
  *(undefined1 *)(iVar1 + 0x77) = 0;
  FUN_1000f204(iVar1);
  return;
}


