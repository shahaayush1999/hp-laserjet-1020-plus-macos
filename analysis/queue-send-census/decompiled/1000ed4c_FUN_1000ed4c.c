/* Function: 1000ed4c FUN_1000ed4c */


void FUN_1000ed4c(int param_1)

{
  int iVar1;
  undefined4 local_30 [3];
  int *piStack_24;

  piStack_24 = (int *)hp1020_runtime_service_candidate(0x10,1);
  local_30[0] = 0x2f;
  *(undefined2 *)(piStack_24 + 3) = *(undefined2 *)(*(int *)(param_1 + 0xc) + 0x6c);
  iVar1 = *(int *)(*(int *)(param_1 + 0xc) + 0x48);
  *piStack_24 = iVar1;
  piStack_24[2] = (uint)*(byte *)(*(int *)(param_1 + 0xc) + 0x6a);
  if (iVar1 == 0) {
    piStack_24[1] = 0;
  }
  else {
    piStack_24[1] = *(int *)(*(int *)(param_1 + 0xc) + 0x58);
  }
  hp1020_queue_send_candidate(10,local_30);
  return;
}
