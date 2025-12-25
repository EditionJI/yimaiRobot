from DrissionPage import ChromiumPage
import time

def main():
    page = ChromiumPage()
    print("已连接浏览器，开始调试库存区间选择...")

    try:
        # 1. 定位下拉框触发器
        print("正在寻找 '请选择' 下拉框...")
        
        triggers = page.eles('css:input[placeholder="请选择"]')
        visible_triggers = [t for t in triggers if t.states.is_displayed]
        
        if not visible_triggers:
            print("错误：未找到任何可见的 '请选择' 输入框")
            return
        
        # 取最后一个可见的
        target_trigger = visible_triggers[-1]
        print(f"找到 {len(visible_triggers)} 个可见下拉框，选择最后一个")

        # 尝试打开下拉框
        # 检查是否有可见的下拉菜单容器
        dropdowns = page.eles('css:div.el-select-dropdown')
        visible_dropdown = None
        for dd in dropdowns:
            if dd.states.is_displayed:
                visible_dropdown = dd
                break
                
        if not visible_dropdown:
            print("当前无可见下拉菜单，尝试点击打开...")
            # 点击父级 div 以防 input 被遮挡
            trigger_parent = target_trigger.parent()
            try:
                trigger_parent.click()
                print("点击了父级")
            except:
                target_trigger.click()
                print("点击了 input")
            
            time.sleep(1)
        else:
            print("检测到下拉菜单已处于打开状态")

        # 等待选项出现
        try:
            # 等待可见的 li
            page.wait.ele('css:div.el-select-dropdown:not([style*="display: none"]) li.el-select-dropdown__item', timeout=3)
            print("下拉选项已就绪")
        except:
            print("等待下拉选项超时")

        # 2. 选上所有选项
        targets = ["0", "1-5", "5-10", "10-20", "20以上"]
        
        # 再次获取可见容器
        dropdowns = page.eles('css:div.el-select-dropdown')
        target_dropdown = None
        for dd in dropdowns:
            if dd.states.is_displayed:
                target_dropdown = dd
        
        if not target_dropdown:
             print("错误：操作后仍未找到可见下拉菜单容器")
             return
             
        print(f"定位到下拉菜单容器: {target_dropdown}")
        
        # 在该容器内找选项
        options = target_dropdown.eles('css:li.el-select-dropdown__item')
        print(f"在容器内找到 {len(options)} 个选项")
        
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
                        print(f"已勾选 '{t}'")
                        time.sleep(0.1)
                    except Exception as click_err:
                        print(f"点击选项 '{t}' 失败，尝试 JS 点击: {click_err}")
                        page.run_js('arguments[0].click()', target_opt)
                        time.sleep(0.1)
            else:
                print(f"警告：在当前下拉菜单中未找到选项 '{t}'")

        # 3. 收起下拉菜单
        print("准备收起下拉菜单...")
        
        # 策略: 点击 body 左上角安全区域
        try:
            # 移动鼠标到 (1,1) 并点击
            page.actions.move(1, 1).click()
            print("已点击页面左上角收起下拉菜单")
        except Exception as e:
            print(f"点击空白处失败: {e}")
            # 备用：按 ESC
            page.actions.type('ESC')
            print("发送 ESC 键")

        time.sleep(0.5)
        
        # 4. 鼠标移开
        page.actions.move(0, 0)
        print("鼠标已移开")
        time.sleep(0.5)
        
        # 5. 点击确定
        print("正在寻找确定按钮...")
        
        # 策略1: 全局查找所有可见的“确定”按钮 (el-button--primary)
        confirm_btns = page.eles('tag:button@@class:el-button--primary')
        
        visible_confirms = []
        for btn in confirm_btns:
            if btn.states.is_displayed and "确定" in btn.text:
                visible_confirms.append(btn)
        
        if visible_confirms:
            # 通常最上层的弹窗按钮在最后
            target_confirm = visible_confirms[-1]
            print(f"选择最后一个可见确定按钮")
            target_confirm.click()
            print("已点击确定按钮")
        else:
            print("全局未找到可见的确定按钮")

    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    main()
