class LibaryReport:
    def number_to_words_vn(num):
        units = ["", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
        tens = ["", "mười", "hai mươi", "ba mươi", "bốn mươi", "năm mươi", "sáu mươi", "bảy mươi", "tám mươi", "chín mươi"]
        big_units = ["", "nghìn", "triệu", "tỷ", "nghìn tỷ", "triệu tỷ"]
        def convert_part(num):
            if num == 0:
                return ""
            hundreds = num // 100
            tens_place = (num % 100) // 10
            ones = num % 10
            result = ""
            if hundreds > 0:
                result += units[hundreds] + " trăm"
            
            if tens_place > 0:
                if tens_place == 1:
                    result += " mười"
                else:
                    result += " " + tens[tens_place]
            if ones > 0:
                if tens_place != 0 and ones == 1:
                    result += " mốt"
                else:
                    result += " " + units[ones]
            return result.strip()
        if num == 0:
            return "Không"
        num_str = str(num)
        result = ""
        unit_index = 0
        while len(num_str) > 0:
            part = num_str[-3:]
            num_str = num_str[:-3]
            part_value = int(part)
            
            if part_value != 0:
                part_result = convert_part(part_value)
                result = f"{part_result} {big_units[unit_index]} " + result
            unit_index += 1
        return result.strip() + " đồng"
