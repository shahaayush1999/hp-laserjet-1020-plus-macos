/* Function: 10010fd0 hp1020_event_flag_set_candidate */


/* WARNING: Control flow encountered bad instruction data */

void hp1020_event_flag_set_candidate(uint *param_1)

{
  bool bVar1;
  uint uVar2;
  int *piVar3;
  int *piVar4;
  code *pcVar5;
  int iVar6;
  undefined4 local_30;
  int iStack_2c;
  uint uStack_28;
  undefined4 uStack_24;
  
  bVar1 = true;
  piVar3 = (int *)(PTR_DAT_1000647c + *param_1 * 0x18);
  if (piVar3[5] != 1) goto switchD_10010ff5_default;
  switch(piVar3[2]) {
  case 0:
    uVar2 = (uint)*(byte *)piVar3[1];
    break;
  case 1:
    uVar2 = (uint)*(ushort *)piVar3[1];
    break;
  case 2:
    uVar2 = *(uint *)piVar3[1];
    break;
  case 3:
  case 4:
    if (*(short *)(piVar3 + 4) != 0) {
                    /* WARNING: Bad instruction - Truncating control flow here */
      halt_baddata();
    }
  default:
    goto switchD_10010ff5_default;
  }
  bVar1 = uVar2 == 0;
switchD_10010ff5_default:
  if (bVar1) {
    hp1020_sys_interface_34_candidate(PTR_DAT_10006474,0xffffffff);
    uVar2 = 0;
    switch(piVar3[2]) {
    case 0:
      uVar2 = (uint)*(byte *)param_1[1];
      *(byte *)piVar3[1] = *(byte *)param_1[1];
      break;
    case 1:
      uVar2 = (uint)*(ushort *)param_1[1];
      *(ushort *)piVar3[1] = *(ushort *)param_1[1];
      break;
    case 2:
      uVar2 = *(uint *)param_1[1];
      *(uint *)piVar3[1] = uVar2;
      break;
    case 3:
      FUN_10016a38(piVar3[1],param_1[1],*(undefined2 *)(piVar3 + 4));
      uVar2 = 0;
      break;
    case 4:
      FUN_1001b38c(piVar3[1],param_1[1],*(undefined2 *)(piVar3 + 4));
      uVar2 = 0;
    }
    if (((*(char *)(piVar3 + 3) != '\0') && (*param_1 < 0x17)) &&
       (*(char *)((int)piVar3 + 0xd) = *(char *)((int)piVar3 + 0xd) + '\x01',
       (int)(*(byte *)(piVar3 + 3) - 1) < (int)(uint)*(byte *)((int)piVar3 + 0xd))) {
      hp1020_sys_interface_16_candidate(PTR_DAT_1000646c,1,0);
    }
    hp1020_sys_interface_37_candidate(PTR_DAT_10006474);
    iVar6 = *piVar3;
    if (*(int *)(PTR_DAT_10006490 + iVar6 * 4) != 0) {
      local_30 = 0x2d;
      if ((uint)piVar3[2] < 3) {
        uStack_24 = 2;
      }
      else if ((uint)piVar3[2] < 5) {
        uStack_24 = 1;
      }
      piVar4 = (int *)(PTR_DAT_10006490 + iVar6 * 4);
      piVar3 = (int *)(*piVar4 + 0xc);
      iStack_2c = iVar6;
      uStack_28 = uVar2;
      do {
        pcVar5 = (code *)((uint)*(byte *)((int)piVar3 + -1) |
                         (uint)*(byte *)((int)piVar3 + -2) << 8 |
                         (uint)*(byte *)((int)piVar3 + -3) << 0x10 |
                         (uint)*(byte *)(piVar3 + -1) << 0x18);
        if (pcVar5 == (code *)0x0) {
          FUN_10013658((uint)*(byte *)((int)piVar3 + -5) |
                       (uint)*(byte *)((int)piVar3 + -6) << 8 |
                       (uint)*(byte *)((int)piVar3 + -7) << 0x10 |
                       (uint)*(byte *)(piVar3 + -2) << 0x18,&local_30);
        }
        else {
          (*pcVar5)(iVar6,uVar2);
        }
        piVar3 = (int *)*piVar3;
      } while (piVar3 != (int *)(*piVar4 + 0xc));
    }
  }
  hp1020_sys_interface_67_candidate(*param_1);
  return;
}


