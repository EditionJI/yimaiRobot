import re
import time
import pandas as pd
import ctypes
import random
from DrissionPage import ChromiumPage

def prevent_lock_screen():
    """
    通过微小移动鼠标防止系统锁屏
    """
    try:
        # 移动鼠标相对位置 (dx, dy)
        # MOUSEEVENTF_MOVE = 0x0001
        # 随机微小移动
        x = random.choice([-1, 1])
        y = random.choice([-1, 1])
        ctypes.windll.user32.mouse_event(0x0001, x, y, 0, 0)
        time.sleep(0.05)
        # 移回来
        ctypes.windll.user32.mouse_event(0x0001, -x, -y, 0, 0)
        # print("执行防锁屏鼠标抖动") # 调试日志
    except Exception as e:
        print(f"防锁屏操作失败: {e}")

def process_keyword(page, keyword):
    """
    处理单个关键词的完整流程
    """
    # 确保 keyword 是字符串
    keyword = str(keyword).strip()
    if not keyword:
        print("跳过空关键词")
        return
        
    print(f"\n=== 开始处理关键词: {keyword} ===")
    
    # 1. 定位到“英文名”栏并在后面的输入框输入
    try:
        # 优化方案：直接通过 placeholder 定位
        # placeholder="多个英文名用英文逗号隔开"
        input_box = page.ele('css:textarea[placeholder="多个英文名用英文逗号隔开"]')
        
        if input_box:
            input_box.clear()
            input_box.input(keyword)
            print(f"已输入 '{keyword}'")
        else:
            # 回退策略：如果 placeholder 变了，尝试模糊匹配或之前的逻辑
            print("警告：通过 placeholder 精确匹配失败，尝试模糊匹配...")
            input_box = page.ele('css:textarea[placeholder*="英文名"]')
            if input_box:
                input_box.clear()
                input_box.input(keyword)
                print(f"已输入 '{keyword}' (模糊匹配)")
            else:
                 # 原有的复杂逻辑作为最后的防线
                 english_name_label = page.ele('text:英文名')
                 if english_name_label:
                     next_ele = english_name_label.next()
                     if next_ele:
                        input_box = next_ele.ele('tag:textarea') or next_ele.ele('tag:input') or next_ele
                        if input_box.tag in ['input', 'textarea']:
                            input_box.clear()
                            input_box.input(keyword)
                            print(f"已输入 '{keyword}' (标签定位)")
                            return

            if not input_box:
                print("错误：未找到'英文名'输入框")
                return

    except Exception as e:
        print(f"输入步骤出错: {e}")
        return

    # 2. 点击“查询”按钮
    try:
        # 优化方案：组合定位
        search_btn = None
        # 1. 找包含搜索图标的 primary button
        icon_btn = page.ele('css:button.el-button--primary i.el-icon-search')
        if icon_btn:
            search_btn = icon_btn.parent()
            
        # 2. 如果没找到，找文本为 "查询" 的 primary button
        if not search_btn:
            search_btn = page.ele('css:button.el-button--primary@@text:查询')
            
        # 3. 回退策略
        if not search_btn:
            reset_btn = page.ele('text:重置')
            if reset_btn:
                search_btn = reset_btn.next('tag:button')

        if search_btn and search_btn.states.is_displayed:
            search_btn.click()
            print("已点击'查询'按钮")
            time.sleep(2)
        else:
            print("错误：未找到可见的'查询'按钮")
            return
    except Exception as e:
        print(f"查询步骤出错: {e}")
        return

    # 3. 检测分页总数
    has_products = False
    try:
        pagination_ele = page.ele(r're:共\s*\d+\s*条', timeout=3)
        if not pagination_ele:
            pagination_ele = page.ele('x://*[contains(normalize-space(.),"共") and contains(normalize-space(.),"条")]', timeout=2)
        
        page_source = page.html
        count = 0
        
        if pagination_ele:
            text = pagination_ele.text
            # print(f"检测到分页信息: {text}") # 日志太冗长，已移除
            matches = re.findall(r'共\s*(\d+)\s*条', text)
            if matches:
                count = int(matches[-1])
        elif page_source:
            # 尝试从源码匹配
            matches = re.findall(r'共\s*(\d+)\s*条', page_source)
            if matches:
                count = int(matches[-1])
                print(f"从源码检测到分页信息: 共 {count} 条")
        
        if count > 0:
            print(f"分页数 {count} > 0，判定为有商品，强制执行后续操作")
            has_products = True
        else:
            # 再次确认暂无数据
            no_data = page.ele('text:暂无数据', timeout=1)
            if no_data:
                print("发现'暂无数据'，且分页数为0，判定为无商品")
            else:
                if count == 0:
                    print("分页数为0，判定为无商品")
            
            print(">>> 跳过后续导出操作")
            return

    except Exception as e:
        print(f"检测分页出错: {e}")
        return

    if not has_products:
        return

    # 4. 鼠标移动到“导出”按钮... (后续逻辑保持不变，只需缩进调整)
    # ... (原有代码逻辑移入此处)
    perform_export(page)

def perform_export(page):
    # 封装导出逻辑，避免主函数过长
    try:
        # 4. 导出菜单逻辑 (优化后的)
        export_btn = None
        export_elements = page.eles('x://*[contains(text(), "导出")]')
        for ele in export_elements:
             if ele.states.is_displayed and ele.text.strip() == "导出":
                 export_btn = ele
                 break
        
        if not export_btn:
            export_btn = page.ele('text:^[\s]*导出[\s]*$')

        if export_btn:
            try:
                if export_btn.states.is_displayed:
                    export_btn.hover()
            except:
                pass
            
            time.sleep(0.5)
            export_basic_info = page.ele('text:导出基本信息', timeout=2)
            
            if export_basic_info and export_basic_info.states.is_displayed:
                export_basic_info.click()
                print("已点击'导出基本信息'")
            else:
                try:
                   export_btn.click()
                except:
                   page.run_js('arguments[0].click()', export_btn)
                   
                time.sleep(0.5)
                export_basic_info = page.ele('text:导出基本信息', timeout=2)
                if export_basic_info:
                    export_basic_info.click()
                    print("已点击'导出基本信息'")
                else:
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
        # ... (简化后的复选框逻辑)
        section_title = page.ele('text:选中字段', timeout=5)
        if not section_title:
             print("错误：未找到'选中字段'标题")
             return
             
        container = section_title.parent()
        if container.tag not in ['div', 'section']: container = container.parent()
        target_header = container.ele('text:字段名称')
        
        if not target_header:
             # 全局搜索回退
             all_headers = page.eles('text:字段名称')
             for h in all_headers:
                 if h.states.is_displayed:
                     target_header = h
                     break
        
        if not target_header:
            print("错误：未找到可见的'字段名称'表头")
            return

        row_container = None
        current = target_header
        for i in range(6):
            parent = current.parent()
            if not parent: break
            if parent.tag == 'tr' or "序号" in parent.text:
                row_container = parent
                break
            current = parent
            
        if not row_container:
            print("错误：未找到表头行容器")
            return
            
        checkboxes = row_container.eles('.el-checkbox__inner')
        if not checkboxes: checkboxes = row_container.eles('tag:input@@type=checkbox')
            
        if checkboxes:
            target_cb = checkboxes[-1] 
            is_checked = "is-checked" in (target_cb.attr('class') or "")
            if not is_checked:
                parent = target_cb.parent()
                if parent and "is-checked" in (parent.attr('class') or ""):
                    is_checked = True
            
            if is_checked:
                print("复选框已是勾选状态")
            else:
                try:
                    target_cb.click(by_js=True) # 直接JS点击
                    print("已点击表头复选框(JS)")
                except:
                    target_cb.click()
                time.sleep(0.5)
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
        primary_buttons = page.eles('css:button.el-button--primary')
        for btn in primary_buttons:
            if btn.states.is_displayed and "导出" in btn.text:
                modal_export = btn # 取最后一个
        
        if modal_export:
            modal_export.click()
            print("已点击弹窗内的'导出'按钮")
        else:
            print("错误：未找到弹窗内的'导出'按钮")
            return
    except Exception as e:
        print(f"点击导出按钮出错: {e}")
        return

    # 7. 弹窗2：库存区间
    try:
        print(f"[{time.time()}] 等待'库存区间'弹窗...")
        page.ele('text:库存区间', timeout=5)
        
        triggers = page.eles('css:input[placeholder="请选择"]')
        visible_triggers = [t for t in triggers if t.states.is_displayed]
        
        if not visible_triggers:
             print("错误：未找到任何可见的 '请选择' 输入框")
             return
             
        target_trigger = visible_triggers[-1]
        
        # 打开下拉框
        dropdowns = page.eles('css:div.el-select-dropdown')
        visible_dropdown = None
        for dd in dropdowns:
            if dd.states.is_displayed:
                visible_dropdown = dd
                break
                
        if not visible_dropdown:
            try:
                target_trigger.parent().click()
            except:
                target_trigger.click()
            time.sleep(0.5)

        # 选所有选项
        targets = ["0", "1-5", "5-10", "10-20", "20以上"]
        
        # 找可见下拉容器
        dropdowns = page.eles('css:div.el-select-dropdown')
        target_dropdown = None
        for dd in dropdowns:
            if dd.states.is_displayed:
                target_dropdown = dd
        
        if target_dropdown:
            options = target_dropdown.eles('css:li.el-select-dropdown__item')
            for t in targets:
                target_opt = None
                for opt in options:
                    if opt.text.strip() == t:
                        target_opt = opt
                        break
                
                if target_opt:
                    if "selected" not in (target_opt.attr('class') or ""):
                        page.run_js('arguments[0].click()', target_opt)
        
        # 收起下拉
        try:
            page.actions.move(1, 1).click()
        except:
            page.actions.type('ESC')
        page.actions.move(0, 0)
        
    except Exception as e:
        print(f"库存区间选择出错: {e}")

    # 8. 最终确定
    try:
        confirm_btns = page.eles('tag:button@@class:el-button--primary')
        visible_confirms = [b for b in confirm_btns if b.states.is_displayed and "确定" in b.text]
        
        if visible_confirms:
            visible_confirms[-1].click()
            print("已点击确定按钮，任务完成")
        else:
            print("全局未找到可见的确定按钮")
            
    except Exception as e:
        print(f"点击确定按钮出错: {e}")


def main():
    page = ChromiumPage()
    print("已连接到浏览器")
    
    # 读取 Excel
    excel_path = r"d:\AI Agent projects\yimaiRPA\11月亚马逊筛选数据.xlsx"
    try:
        # header=None 表示没有表头，读取所有行
        df = pd.read_excel(excel_path, header=None)
        # 假设关键词在第一列 (索引 0)
        # dropna() 去除空值
        keywords = df.iloc[:, 0].dropna().astype(str).tolist()
        print(f"成功读取 Excel，共找到 {len(keywords)} 个关键词")
    except Exception as e:
        print(f"读取 Excel 文件失败: {e}")
        return

    # 从第 1852 个词开始
    start_from = 1852
    
    for index, kw in enumerate(keywords):
        current_num = index + 1
        if current_num < start_from:
            continue
            
        print(f"\n[{current_num}/{len(keywords)}] 正在处理: {kw}")
        process_keyword(page, kw)
        
        # 执行防锁屏操作
        prevent_lock_screen()
        
        # 任务间隔，防止操作过快
        time.sleep(2)

if __name__ == "__main__":
    main()
