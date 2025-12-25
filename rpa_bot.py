import re
import time
from DrissionPage import ChromiumPage

def main():
    # 连接到已打开的浏览器
    page = ChromiumPage()
    print("已连接到浏览器")

    # 1. 定位到“英文名”栏并在后面的输入框输入 “vow books”
    try:
        # 寻找包含“英文名”文本的元素，通常是 label 或 span
        # 使用 flexible locators
        english_name_label = page.ele('text:英文名')
        if not english_name_label:
            print("错误：未找到'英文名'标签")
            return

        # 1. 尝试找它后面的兄弟节点中的输入框
        # 很多时候 label 和 input 并不是直接兄弟，而是相邻容器
        next_ele = english_name_label.next()
        
        input_box = None
        if next_ele:
            # 检查下一个元素本身是不是输入框
            if next_ele.tag in ['input', 'textarea']:
                input_box = next_ele
            else:
                # 检查下一个元素内部有没有输入框
                input_box = next_ele.ele('tag:textarea') or next_ele.ele('tag:input')
        
        # 2. 如果还没找到，尝试从父级找
        if not input_box:
            parent = english_name_label.parent()
            # 在父级中找 textarea，且不包括 english_name_label 本身
            # 这里简单粗暴地找父级下的所有 input/textarea，取位置在 label 之后的
            # 或者直接找 label 父级的下一个兄弟
            
            # 尝试找父级的下一个兄弟（有些布局是 Label div + Input div）
            parent_next = parent.next()
            if parent_next:
                input_box = parent_next.ele('tag:textarea') or parent_next.ele('tag:input')

        if input_box:
            input_box.clear()
            input_box.input("vow books")
            print("已输入 'vow books'")
        else:
            print("错误：未找到'英文名'后的输入框")
            return

    except Exception as e:
        print(f"输入步骤出错: {e}")
        return

    # 2. 点击“查询”按钮
    try:
        # 尝试多种定位方式
        # 1. 查找文本完全匹配“查询”的按钮
        search_btn = page.ele('tag:button@@text:^查询$')
        
        # 2. 如果没找到，找文本包含“查询”且不是“重置”的按钮
        if not search_btn:
            # 排除掉可能存在的其他查询相关按钮，只找那个主要的蓝色按钮
            # 通常蓝色按钮会有特定的 class，比如 ant-btn-primary 或 el-button--primary
            # 但这里我们尽量用通用特征。从图上看，它在“重置”按钮右边
            
            reset_btn = page.ele('text:重置')
            if reset_btn:
                # 找重置按钮后面的兄弟
                search_btn = reset_btn.next('tag:button')
        
        # 3. 实在找不到，尝试通过图标定位（如果有搜索图标）
        # 或者直接找包含“查询”文本的任何可点击元素
        if not search_btn:
             search_btn = page.ele('text:查询')

        if search_btn:
            # 确保它是可见的
            if search_btn.states.is_displayed:
                search_btn.click()
                print("已点击'查询'按钮")
                # 等待数据加载，这里简单sleep一下，配合后面的元素等待
                time.sleep(2)
            else:
                print("错误：找到'查询'按钮，但它不可见")
                return
        else:
            print("错误：未找到'查询'按钮")
            return
    except Exception as e:
        print(f"查询步骤出错: {e}")
        return

    # 3. 检测分页总数
    has_products = False
    try:
        # 尝试寻找“共 X 条”的文本
        # 策略：
        # 1. 优先检测分页数（re:共 \d+ 条）
        # 2. 如果检测到且数量 > 0 -> 强制认为有商品（has_products = True）
        # 3. 如果检测到且数量 = 0 -> 强制认为无商品（has_products = False），并立即返回
        # 4. 如果完全没检测到分页信息 -> 进入回退逻辑（检查暂无数据等）
        
        # 使用较短的超时时间检测分页，因为如果加载出来了应该很快
        pagination_ele = page.ele(r're:共\s*\d+\s*条', timeout=3)
        if not pagination_ele:
            pagination_ele = page.ele('x://*[contains(normalize-space(.),"共") and contains(normalize-space(.),"条")]', timeout=2)
        page_source = page.html
        
        if pagination_ele or page_source:
            text = pagination_ele.text if pagination_ele else ""
            print(f"检测到分页信息: {text}" if text else "检测到分页信息（来自页面源）")
            matches = re.findall(r'共\s*(\d+)\s*条', page_source or text)
            if matches:
                count = int(matches[-1])
                if count > 0:
                    print(f"分页数 {count} > 0，判定为有商品，强制执行后续操作")
                    has_products = True
                else:
                    print("分页数 = 0，判定为无商品，跳过后续操作")
                    return
        else:
            # 极其罕见的情况：没找到分页数
            print("警告：未检测到分页信息（极其罕见），执行回退逻辑")
            
            # 回退逻辑：检查是否有“暂无数据”
            no_data = page.ele('text:暂无数据', timeout=2)
            if not no_data:
                 print("未发现'暂无数据'提示，假定存在商品")
                 has_products = True
            else:
                 print("发现'暂无数据'，跳过后续操作")
                 return

    except Exception as e:
        print(f"检测分页出错: {e}")
        return

    if not has_products:
        return

    # 4. 鼠标移动到“导出”按钮，点击“导出基本信息”
    try:
        # 找到“批量标记为已刊登”旁边的“导出”按钮
        export_btn = None
        
        # 优化策略：优先使用之前成功的策略3 -> 查找所有包含'导出'的可见元素
        print("查找所有包含'导出'的元素...")
        # 使用 xpath 查找所有包含导出的元素
        export_elements = page.eles('x://*[contains(text(), "导出")]')
        for ele in export_elements:
             if ele.states.is_displayed:
                 # 排除掉一些干扰项
                 txt = ele.text.strip()
                 # 只要是“导出”两个字，或者是按钮
                 if txt == "导出":
                     export_btn = ele
                     print(f"找到可见导出按钮: {ele}")
                     break
        
        # 如果策略3没找到，尝试之前的策略1：文本精确匹配
        if not export_btn:
            print("未找到，尝试精确匹配...")
            export_btn = page.ele('text:^[\s]*导出[\s]*$')

        if export_btn:
            # 使用 JS 点击通常更稳健，或者 DrissionPage 的 click(by_js=True)
            # 先尝试普通悬停
            found_menu = False
            
            # 这里的 candidates 逻辑其实可以简化，既然我们已经找到了 export_btn
            try:
                # 尝试 hover, 如果报错(比如元素无大小)，尝试 hover 父级或 JS hover
                # 但 DrissionPage 的 hover 如果元素不可见会报错
                # 确保元素可见
                if export_btn.states.is_displayed:
                    export_btn.hover()
                else:
                    print("导出按钮状态变为不可见，尝试重新定位...")
                    # 重新定位
                    export_btn = page.ele('x://*[contains(text(), "导出") and not(contains(text(), "基本信息"))]')
                    if export_btn: export_btn.hover()
            except Exception as e:
                print(f"Hover 失败: {e}，尝试直接查找菜单项...")
                pass
            
            time.sleep(0.5) # 给一点时间让菜单出来
            
            # 直接查找菜单项，不管 hover 是否成功
            export_basic_info = page.ele('text:导出基本信息', timeout=2)
            
            if export_basic_info and export_basic_info.states.is_displayed:
                export_basic_info.click()
                print("已点击'导出基本信息'")
                found_menu = True
            else:
                # 尝试点击一下导出按钮（有时候点击也能触发下拉）
                print("未找到菜单，尝试点击导出按钮...")
                try:
                   export_btn.click()
                except:
                   page.run_js('arguments[0].click()', export_btn)
                   
                time.sleep(0.5)
                export_basic_info = page.ele('text:导出基本信息', timeout=2)
                if export_basic_info:
                    export_basic_info.click()
                    print("已点击'导出基本信息'")
                    found_menu = True

            if not found_menu:
                print("错误：下拉菜单中未找到'导出基本信息'")
                return
        else:
            print("错误：未找到'导出'按钮")
            return
    except Exception as e:
        print(f"点击导出菜单出错: {e}")
        return

    # 5. 弹窗1：勾选全选框
    try:
        print("开始寻找弹窗内的复选框...")
        
        # 1. 定位上下文 "选中字段"
        section_title = page.ele('text:选中字段')
        if not section_title:
             print("错误：未找到'选中字段'标题")
             return
        print(f"找到区域标题: {section_title.text}")
        
        # 2. 找到对应的表格头 "字段名称"
        # 策略：在 section_title 的父容器内查找
        container = section_title.parent()
        # 如果父容器太小（比如只是个标题div），往上找一级
        if container.tag != 'div' and container.tag != 'section':
             container = container.parent()
             
        target_header = container.ele('text:字段名称')
        # 如果在容器内没找到，尝试全局找，但过滤位置
        if not target_header:
             print("在容器内未找到'字段名称'，尝试全局搜索并匹配位置")
             all_headers = page.eles('text:字段名称')
             for h in all_headers:
                 if h.states.is_displayed:
                     # 简单的位置检查：它应该在 section_title 之后
                     # 这里暂且假设第一个可见的就是
                     target_header = h
                     break
        
        if not target_header:
            print("错误：未找到可见的'字段名称'表头")
            return
            
        print(f"锁定目标表头: {target_header}")

        # 3. 向上寻找表头行 (TR)
        row_container = None
        current = target_header
        for i in range(6):
            parent = current.parent()
            if not parent: break
            if parent.tag == 'tr' or "序号" in parent.text:
                row_container = parent
                print(f"找到表头行容器 (层级 {i+1}): {row_container.tag}")
                break
            current = parent
            
        if not row_container:
            print("错误：未找到表头行容器")
            return
            
        # 4. 在行内寻找复选框并点击
        # 尝试查找所有的 .el-checkbox__inner 或 input
        checkboxes = row_container.eles('.el-checkbox__inner')
        if not checkboxes:
            checkboxes = row_container.eles('tag:input@@type=checkbox')
            
        if checkboxes:
            print(f"在表头行找到 {len(checkboxes)} 个复选框")
            # 通常全选框是唯一的，或者是最后一个（如果前面是序号）
            # 用户说在“字段名称”右边的标题栏 -> 可能是最后一个
            target_cb = checkboxes[-1] 
            
            # 尝试获取 wrapper 和 label
            cb_wrapper = target_cb.parent() # .el-checkbox__input
            cb_label = cb_wrapper.parent() if cb_wrapper else None # .el-checkbox
            
            # 检查是否已勾选
            is_checked = False
            if "is-checked" in (target_cb.attr('class') or ""): is_checked = True
            if cb_wrapper and "is-checked" in (cb_wrapper.attr('class') or ""): is_checked = True
            if cb_label and "is-checked" in (cb_label.attr('class') or ""): is_checked = True
            
            if is_checked:
                print("复选框已是勾选状态")
            else:
                print("尝试点击复选框...")
                # 尝试组合拳：点击 label -> 点击 wrapper -> JS点击
                if cb_label and cb_label.tag == 'label':
                    cb_label.click()
                elif cb_wrapper:
                    cb_wrapper.click()
                else:
                    target_cb.click()
                    
                time.sleep(0.5)
                
                # 再次检查
                if cb_wrapper and "is-checked" not in (cb_wrapper.attr('class') or ""):
                    print("普通点击无效，尝试 JS 点击 wrapper")
                    cb_wrapper.click(by_js=True)
                    time.sleep(0.5)
                    
                if cb_wrapper and "is-checked" not in (cb_wrapper.attr('class') or ""):
                    print("JS点击wrapper无效，尝试 JS 点击 inner")
                    target_cb.click(by_js=True)
        else:
            print("错误：在表头行内未找到任何复选框")
            return

    except Exception as e:
        print(f"复选框操作出错: {e}")
        return

    # 6. 点击弹窗内的“导出”按钮
    try:
        print("准备点击弹窗内的'导出'按钮...")
        
        modal_export = None
        
        # 用户提示的按钮代码: <button ... class="el-button el-button--primary ..."><span>导出</span></button>
        # 策略：查找所有可见的 el-button--primary 按钮，并筛选文本为“导出”的
        
        # 1. 查找所有主要按钮 (el-button--primary)
        primary_buttons = page.eles('css:button.el-button--primary')
        print(f"找到 {len(primary_buttons)} 个主要按钮")
        
        target_btns = []
        for btn in primary_buttons:
            # 检查可见性
            if btn.states.is_displayed:
                # 检查文本，允许包含空白
                if "导出" in btn.text:
                    target_btns.append(btn)
                    print(f"候选主要按钮: text='{btn.text}'")
        
        if target_btns:
            # 通常弹窗在最上层，取最后一个
            modal_export = target_btns[-1]
            print(f"选中最后一个可见的'导出'主要按钮")
        else:
            print("未找到'导出'主要按钮，尝试通用按钮搜索")
            # 回退策略：查找所有按钮
            all_btns = page.eles('tag:button')
            visible_btns = []
            for btn in all_btns:
                if btn.states.is_displayed and "导出" in btn.text:
                     # 排除之前的菜单按钮
                     if "基本信息" in btn.text or "商品费" in btn.text: continue
                     visible_btns.append(btn)
                     print(f"候选通用按钮: text='{btn.text}', class={btn.attr('class')}")
            
            if visible_btns:
                modal_export = visible_btns[-1]
                print("选中最后一个可见的通用'导出'按钮")

        if modal_export:
            # 打印详细信息确认
            print(f"即将点击: tag={modal_export.tag}, text='{modal_export.text}', class='{modal_export.attr('class')}'")
            modal_export.click()
            print("已点击弹窗内的'导出'按钮")
        else:
            print("错误：未找到弹窗内的'导出'按钮")
            
            # 调试：打印一下页面上所有的“导出”相关元素
            print("调试信息：页面上所有包含'导出'的元素:")
            debug_eles = page.eles('text:导出')
            for de in debug_eles:
                print(f"  Tag: {de.tag}, Visible: {de.states.is_displayed}, Text: {de.text[:20]}..., Class: {de.attr('class')}")
            return

    except Exception as e:
        print(f"点击导出按钮出错: {e}")
        return

    # 6. 弹窗2：选择库存区间
    try:
        start_time = time.time()
        print(f"[{time.time()}] 等待'库存区间'弹窗...")
        page.ele('text:库存区间', timeout=5)
        print(f"[{time.time()}] 弹窗已出现")
        
        # 定位逻辑：找到"库存区间"标签，然后找后面的输入框/下拉触发器
        # ... (定位 trigger 逻辑优化)
        
        # 尝试2: 通过 placeholder 定位
        triggers = page.eles('css:input[placeholder="请选择"]')
        visible_triggers = [t for t in triggers if t.states.is_displayed]
        
        if not visible_triggers:
             print("错误：未找到任何可见的 '请选择' 输入框")
             return
             
        # 取最后一个可见的
        target_trigger = visible_triggers[-1]
        print(f"[{time.time()}] 找到可见下拉框触发器")

        # 尝试打开下拉框
        # 检查是否有可见的下拉菜单容器
        dropdowns = page.eles('css:div.el-select-dropdown')
        visible_dropdown = None
        for dd in dropdowns:
            if dd.states.is_displayed:
                visible_dropdown = dd
                break
                
        if not visible_dropdown:
            print(f"[{time.time()}] 当前无可见下拉菜单，尝试点击打开...")
            trigger_parent = target_trigger.parent()
            try:
                trigger_parent.click()
                print("点击了父级")
            except:
                target_trigger.click()
                print("点击了 input")
            time.sleep(0.5)
        else:
            print("检测到下拉菜单已处于打开状态")

        # 等待选项出现
        try:
            page.wait.ele('css:div.el-select-dropdown:not([style*="display: none"]) li.el-select-dropdown__item', timeout=2)
            print(f"[{time.time()}] 下拉选项已就绪")
        except:
            print("等待下拉选项超时")

        # 2. 选上所有选项
        targets = ["0", "1-5", "5-10", "10-20", "20以上"]
        
        # 策略：找到当前可见的 dropdown 容器
        dropdowns = page.eles('css:div.el-select-dropdown')
        target_dropdown = None
        for dd in dropdowns:
            if dd.states.is_displayed:
                target_dropdown = dd
        
        if not target_dropdown:
             print("错误：操作后仍未找到可见下拉菜单容器")
             return
             
        print(f"[{time.time()}] 定位到下拉菜单容器")
        
        # 在该容器内找选项
        options = target_dropdown.eles('css:li.el-select-dropdown__item')
        
        for t in targets:
            target_opt = None
            for opt in options:
                if opt.text.strip() == t:
                    target_opt = opt
                    break
            
            if target_opt:
                # 检查是否已选
                if "selected" in (target_opt.attr('class') or ""):
                    print(f"选项 '{t}' 已选中")
                else:
                    try:
                        target_opt.click()
                        print(f"[{time.time()}] 已勾选 '{t}'")
                    except Exception as click_err:
                        # 尝试 JS 点击
                        page.run_js('arguments[0].click()', target_opt)
            else:
                print(f"警告：在当前下拉菜单中未找到选项 '{t}'")
        
        # 3. 收起下拉菜单
        print(f"[{time.time()}] 准备收起下拉菜单...")
        try:
            # 移动鼠标到 (1,1) 并点击
            page.actions.move(1, 1).click()
            print("已点击页面左上角收起下拉菜单")
        except:
            page.actions.type('ESC')
            print("发送 ESC 键")
            
        # 4. 鼠标移开
        page.actions.move(0, 0)
        
    except Exception as e:
        print(f"库存区间选择出错: {e}")

    # 7. 点击弹窗上的蓝色的“确定”按钮
    try:
        print(f"[{time.time()}] 正在寻找确定按钮...")
        
        # 策略1: 全局查找所有可见的“确定”按钮 (el-button--primary)
        confirm_btns = page.eles('tag:button@@class:el-button--primary')
        visible_confirms = [b for b in confirm_btns if b.states.is_displayed and "确定" in b.text]
        
        if visible_confirms:
            target_confirm = visible_confirms[-1]
            print(f"[{time.time()}] 选择最后一个可见确定按钮")
            target_confirm.click()
            print(f"[{time.time()}] 已点击确定按钮，任务完成")
        else:
            print("全局未找到可见的确定按钮")
            
    except Exception as e:
        print(f"点击确定按钮出错: {e}")

if __name__ == "__main__":
    main()
