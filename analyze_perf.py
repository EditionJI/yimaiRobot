from DrissionPage import ChromiumPage
import time
import re

def analyze_efficiency(page, keyword):
    """
    专门用于分析搜索到导出步骤效率的函数
    """
    print(f"\n=== 开始分析效率: {keyword} ===")
    start_all = time.time()
    
    # 1. 输入
    t1 = time.time()
    try:
        # 优化方案：直接通过 placeholder 定位
        # 这是一个 textarea，不是 input
        # placeholder="多个英文名用英文逗号隔开"
        input_box = page.ele('css:textarea[placeholder="多个英文名用英文逗号隔开"]')
             
        if input_box:
            input_box.clear()
            input_box.input(keyword)
            print(f"输入耗时: {time.time() - t1:.4f}s")
        else:
            print("未找到输入框 (textarea placeholder匹配失败)")
            # 调试：打印所有可见 textarea
            tas = page.eles('tag:textarea')
            for t in tas:
                if t.states.is_displayed:
                    print(f"可见 textarea placeholder: {t.attr('placeholder')}")
    except Exception as e:
        print(f"输入出错: {e}")

    # 2. 点击查询
    t2 = time.time()
    try:
        # 优化方案：利用提供的 HTML 特征
        # class="el-button el-button--primary el-button--small" 且包含 icon el-icon-search
        # 组合定位：找包含 search icon 的 primary button
        
        # 方式1: 直接找包含 search icon 的按钮
        search_btn = page.ele('css:button.el-button--primary i.el-icon-search')
        # 注意：ele 返回的是 icon，我们要点击的是它的父级 button
        if search_btn:
            search_btn = search_btn.parent()
        
        # 方式2: 如果方式1没找到，找文本为 " 查询 " (注意空格) 的 primary button
        if not search_btn:
            search_btn = page.ele('css:button.el-button--primary@@text:查询')
            
        print(f"查找查询按钮耗时: {time.time() - t2:.4f}s")
        
        if search_btn:
            search_btn.click()
            print(f"点击查询耗时: {time.time() - t2:.4f}s") # 累计时间
            
            # 3. 等待加载
            t_wait = time.time()
            time.sleep(2) 
            print(f"硬等待耗时: {time.time() - t_wait:.4f}s")
        else:
            print("未找到查询按钮")
            
    except Exception as e:
        print(f"查询出错: {e}")

    # 4. 导出
    t3 = time.time()
    try:
        # 当前逻辑：查找所有包含导出的元素 -> 遍历 -> hover -> 找菜单
        
        t_find_export = time.time()
        # 模拟当前逻辑
        export_btn = None
        export_elements = page.eles('x://*[contains(text(), "导出")]')
        for ele in export_elements:
             if ele.states.is_displayed and ele.text.strip() == "导出":
                 export_btn = ele
                 break
        print(f"查找导出按钮耗时: {time.time() - t_find_export:.4f}s")
        
        if export_btn:
            t_menu = time.time()
            try:
                export_btn.hover()
            except:
                pass
            
            # 当前逻辑：死等 0.5s
            time.sleep(0.5)
            
            export_basic_info = page.ele('text:导出基本信息', timeout=2)
            if export_basic_info:
                export_basic_info.click()
                print(f"菜单操作耗时: {time.time() - t_menu:.4f}s")
            
    except Exception as e:
        print(f"导出出错: {e}")

    print(f"总耗时: {time.time() - start_all:.4f}s")

def main():
    page = ChromiumPage()
    analyze_efficiency(page, "vow books")

if __name__ == "__main__":
    main()
