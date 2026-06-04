/* Function: 1000b1d4 FUN_1000b1d4 */


void FUN_1000b1d4(undefined4 param_1)

{
  undefined2 uVar1;
  undefined *puVar2;
  undefined *puVar3;
  int iVar4;
  undefined1 auStack_30 [48];
  
  puVar3 = PTR_s_USTATUS_100060e0;
  puVar2 = PTR_DAT_100060d4;
  if (*(int *)PTR_DAT_100060d8 == 2) {
    uVar1 = *(undefined2 *)(PTR_DAT_100060dc + 4);
    *(undefined4 *)PTR_DAT_100060d4 = *(undefined4 *)PTR_DAT_100060dc;
    *(undefined2 *)(puVar2 + 4) = uVar1;
    hp1020_append_string_to_buffer_candidate(puVar2,puVar3);
    hp1020_append_string_to_buffer_candidate(puVar2,PTR_DAT_100060e4);
    hp1020_append_string_to_buffer_candidate(puVar2,PTR_s_DEVICE_100060e8);
    puVar3 = PTR_DAT_100060ec;
    hp1020_append_string_to_buffer_candidate(puVar2,PTR_DAT_100060ec);
    hp1020_append_string_to_buffer_candidate(puVar2,PTR_DAT_100060f0);
    hp1020_append_string_to_buffer_candidate(puVar2,PTR_DAT_100060f4);
    FUN_1000ae3c(auStack_30,param_1);
    hp1020_append_string_to_buffer_candidate(puVar2,auStack_30);
    hp1020_append_string_to_buffer_candidate(puVar2,puVar3);
    hp1020_append_string_to_buffer_candidate(puVar2,PTR_DAT_100060f8);
    iVar4 = hp1020_strlen_like(puVar2);
    iVar4 = hp1020_alloc_buffer_candidate(iVar4 + 1);
    if (iVar4 == 0) {
      return;
    }
    hp1020_copy_string_candidate(iVar4,puVar2);
    FUN_1000b1c4();
    hp1020_pjl_response_send_candidate(iVar4,1);
  }
  return;
}


