Function 追板();
Begin
    day := IntToDate({day});

    ret := array();
    stock_list := getbk('A股');
    stock_list::begin
        stock_code := mcell;
        stock_name := stockName(stock_code);

        if not (stock_code like 'SZ|SH') then
            continue;

        if stock_name like 'ST|退' then
            continue;

        if not is_trade_day(day, stock_code) then
            continue;

        with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
        begin
            昨日收盘价 := ref(close(), 1);
            今日涨停价 := StockZtClose(day);
            next_day := StockEndTPrevNDay(day, -1);
            明日涨停价 := StockZtClose(next_day);
        end

        if stock_code[3:4] = '30' or stock_code[3:4] = '68' then
        begin
            if count_ratio(今日涨停价, 昨日收盘价) < 15 then
                continue;
        end

        买入 := 计算买入(stock_name, stock_code, day);
        if 买入[0] = 0 then
            continue;

        上市天数 := 计算自定义上市天数(stock_code, day);
        上涨周期 := 寻找上涨起点(stock_name, stock_code, day, 上市天数, 3, 3);
        if 上涨周期 = 0 then
        begin
            上涨起点 := day;
        end
        else
        begin
            with *,array(pn_Stock():stock_code, PN_Cycle():cy_day()) do
            begin
                上涨起点 := StockEndTPrevNDay(day, 上涨周期);
            end
        end
        上涨起点日 := DateToStr(上涨起点);

        涨停 := 计算涨停板(stock_code, day);
        最高价 := 计算最高价(stock_name, stock_code, 上涨起点);
        涨幅 := 计算涨幅(stock_name, stock_code, day, 70);
        金额 := 计算原始金额(stock_name, stock_code, day, 6);
        原始金额 := 金额[0];
        原始金额2 := 金额[1];
        if 原始金额2 = 0 then
            continue;
        首板新高 := 计算100日首板新高(stock_name, stock_code, day);
        次日下午成交额 := 计算次日下午成交额(stock_name, stock_code, next_day, 明日涨停价);
        ma5上涨起始日 := count_ma_start_day(day, stock_code, 5);
        str_ma5上涨起始日 := DateToStr(ma5上涨起始日);
        本轮上涨幅度 := 计算本轮上涨幅度(ma5上涨起始日, stock_code, day);
        本轮上涨涨停板个数 := 计算本轮上涨涨停板个数(ma5上涨起始日, stock_code, day);
        ret &= array(('名称':stock_name, '代码':stock_code,
                '买入价':买入[0], '买入时间':买入[1], '当日已成交金额':买入[2],
                '原始金额':原始金额, '原始金额2':原始金额,
                '涨停拉升':买入[3], 'ma5上涨起始日':str_ma5上涨起始日,
                '本轮上涨幅度':本轮上涨幅度, '本轮上涨涨停板个数':本轮上涨涨停板个数,
                '买入价涨幅3':count_ratio(买入[0], 最高价[0]),
                '买入价涨幅5':count_ratio(买入[0], 最高价[1]),
                '买入价涨幅7':count_ratio(买入[0], 最高价[2]),
                '买入价涨幅10':count_ratio(买入[0], 最高价[3]),
                '买入价涨幅15':count_ratio(买入[0], 最高价[4]),
                '买入价涨幅30':count_ratio(买入[0], 最高价[5]),
                '买入价涨幅60':count_ratio(买入[0], 最高价[6]),
                '1日涨停数':涨停[0], '2日涨停数':涨停[1], '3日涨停数':涨停[2],
                '4日涨停数':涨停[3], '5日涨停数':涨停[4], '6日涨停数':涨停[5],
                '7日涨停数':涨停[6], '10日涨停数':涨停[7],
                '15日涨停数':涨停[8], '30日涨停数':涨停[9],
                '100日内出现5日涨幅超70':涨幅[0],
                '200日内出现5日涨幅超70':涨幅[1],
                '100日首板新高':首板新高, '上涨起点日': 上涨起点日,
                '次日下午成交额':int(次日下午成交额/10000)
                ));
    end;
    return exportjsonstring(ret);
End;

function 计算本轮上涨涨停板个数(before_day, stock_code, day);
begin
    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
    begin
        str_before_day := DateToStr(before_day);
        上市日 := FundGoMarketDate();
        i := 1;
        ret := 0;
        while True do
        begin
            one_day := StockEndTPrevNDay(day, i);
            str_one_day := datetostr(one_day);
            if DateToInt(one_day) < 上市日 then
                break;

            if one_day < before_day then
                break;

            if StockIsZt(one_day) then
                ret += 1;
            i += 1;
        end
    end
    return ret;
end

function 计算本轮上涨幅度(before_day, stock_code, day);
begin
    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
    begin
        str_before_day := DateToStr(before_day);
        上市日 := FundGoMarketDate();
        i := 1;
        ret := 0;
        while True do
        begin
            one_day := StockEndTPrevNDay(day, i);
            str_one_day := datetostr(one_day);
            if DateToInt(one_day) < 上市日 then
                break;

            if one_day < before_day then
                break;
            i += 1;
        end
        昨日收盘价 := StockClose(StockEndTPrevNDay(day, 1));
        上涨起始日收盘价 := StockClose(StockEndTPrevNDay(day, i - 1));
    end
    return count_ratio(昨日收盘价, 上涨起始日收盘价);
end

function count_ma_start_day(day, stock_code, num);
begin
    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
    begin
        上市日 := FundGoMarketDate();
        ret := 0;
        i := 2;
        last_ma := ref(ma(close(), num), 1);
        while True do
        begin
            one_day := StockEndTPrevNDay(day, i);
            if DateToInt(one_day) < 上市日 then
                break;

            one_day_close := StockClose(one_day);
            one_ma := ref(ma(close(), num), i);
            if one_ma <= last_ma then
            begin
                i += 1;
                last_ma := one_ma;
            end
            else
                break;
        end
        return StockEndTPrevNDay(day, i - 1);
    end
end

function 计算次日下午成交额(stock_name, stock_code, next_day, 明日涨停价);
begin
    with *,array(pn_Stock():stock_code, pn_date():next_day, pn_rate():2, pn_rateday():next_day, PN_Cycle():cy_1m()) do
    begin
        data := select
        TimeToStr(["date"]) as "时间",
        ["close"],
        ['amount']
        from markettable datekey next_day+StrToTime("13:25:00") to next_day+StrToTime("13:55:00") of DefaultStockID() end;
    end

    sum_amount := 0;
    for idx in data do
    begin
        if data[idx]['close'] <> 明日涨停价 then
            sum_amount += data[idx]['amount'];
    end
    return sum_amount;
end

function 计算自定义上市天数(stock_code, day);
begin
    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
    begin
        当前日 := DateToInt(day);
        上市日 := FundGoMarketDate();
        if 当前日 = 上市日 then
            return 0;

        上市天数 := StockGoMarketDays();
        assert(上市天数 > 0);

        num := 1;
        while true do
        begin
            下一日 := StockEndTPrevNDay(IntToDate(上市日), -num);
            str_next_day := DateToStr(下一日);

            if 下一日 = day then
                return 0;

            if stockiszt2(下一日) then
                num += 1;
            else
                break;
        end
    end
    return day - 下一日;
end

function 创n日新高(stock_name, stock_code, day, 回溯天数, 创几日新高);
begin
    close1 := ref(close(), 回溯天数);
    for i := 1 to 创几日新高 - 1 do
    begin
        日期3 := DateToStr(StockEndTPrevNDay(day, i + 回溯天数));

        close2 := ref(close(), i + 回溯天数);
        if close1 < close2  then
            return False; // 没创n日新高
    end
    return True;
end

function 几日内创过几日新高(stock_name, stock_code, day, 回溯天数, 几日内, 创几日新高);
begin
    for i := 0 to 几日内 - 1 do
    begin
        日期2 := DateToStr(StockEndTPrevNDay(day, i + 回溯天数)); // 判断日
        if 创n日新高(stock_name, stock_code, day, i + 回溯天数, 创几日新高) then
            return True;
    end
    return False;
end

function 寻找上涨起点(stock_name, stock_code, day, 上市天数, 几日内, 创几日新高);
begin
    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
    begin
        上市日 := StockFirstDay(stock_code);

        if day = 上市日 then
            return 0;

        回溯天数 := 1; // 回溯多少天
        while True do
        begin
            日期1 := DateToStr(StockEndTPrevNDay(day, 回溯天数)); // 回溯日
            回溯日 := StockEndTPrevNDay(day, 回溯天数);

            if 回溯日 = 上市日 then
            begin
                return 回溯天数;
            end

            if stockiszt(回溯日) then
            begin
                回溯天数 += 1; // 当日涨停，继续向前回溯
                continue
            end

            if 几日内创过几日新高(stock_name, stock_code, day, 回溯天数, 几日内, 创几日新高) then
                回溯天数 += 1; // 回溯日n1日内创过n2日新高，继续向前回溯
            else
                break;
        end
    end
    return 回溯天数 - 1;
end

function 计算原始金额(stock_name, stock_code, day, num);
begin
    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
    begin
        data := ref(nday(num, '时间', datetimetostr(sp_time()), '成交金额',amount()), 1);
        if data = 0 or length(data) = 1 then
            return array(0, 0);

        num_amount := 0;
        sum_amount := 0;
        max_amount := 0;
        j := 1;
        for i := length(data) - 1 downto 0 do
        begin
            if stockiszt2(StockEndTPrevNDay(day, j)) = 0 then
            begin
                sum_amount += data[i]['成交金额'];
                num_amount += 1;

                if data[i]['成交金额'] > max_amount then
                    max_amount := data[i]['成交金额'];
            end
            j += 1;
        end
    end

    if num_amount = 0 then
        return array(0, 0);

    ori_sum_amount := sum_amount;
    ori_num_amount := num_amount;
    if num_amount > 1 then
    begin
        sum_amount -= max_amount;
        num_amount -= 1;
    end
    return array(int(sum_amount / num_amount), int(ori_sum_amount / ori_num_amount));
end

function 计算100日首板新高(stock_name, stock_code, day);
begin
    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
    begin
        当日涨停价 := StockZtClose(day);
        昨日涨停 := StockIsZt(StockEndTPrevNDay(day, 1));
        if 昨日涨停 = 1 then
            return 0;

        data := ref(nday(100, '时间', datetimetostr(sp_time()), '收盘价',close()), 1);
        if data = 0 or length(data) <> 100 then
            return 0;

        for i := 0 to 100 do
        begin
            if data[i]['收盘价'] >= 当日涨停价 then
                return 0
        end
    end
    return 1;
end

function 计算涨幅(stock_name, stock_code, day, ratio);
begin
    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
    begin
        for i := 1 to 200 do
        begin
            close1 := ref(close(), i);
            close2 := ref(close(), i + 1);
            close3 := ref(close(), i + 2);
            close4 := ref(close(), i + 3);
            close5 := ref(close(), i + 4);
            close6 := ref(close(), i + 5);

            ratio3 := count_ratio(close1, close4);
            ratio4 := count_ratio(close1, close5);
            if ratio4 > ratio then
            begin
                if count_ratio(close2, close5) > ratio then
                    ratio4 := 0
            end

            ratio5 := count_ratio(close1, close6);
            if ratio5 > ratio then
            begin
                if count_ratio(close2, close6) > ratio then
                    ratio5 := 0;
                if count_ratio(close3, close6) > ratio then
                    ratio5 := 0;
            end

            str_day := DateToStr(StockEndTPrevNDay(day, i));

            if ratio3 > ratio or ratio4 > ratio or ratio5 > ratio then
            begin
                if i <= 100 then
                    return array(1, 1);
                else
                    return array(0, 1);
            end
        end
    end
    return array(0, 0);
end

function 计算最高价(stock_name, stock_code, day);
begin
    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
    begin
        data := ref(nday(60, '时间', datetimetostr(sp_time()), '当日高价',high()), 1);
        if data = 0 then
            return array(0, 0, 0, 0, 0, 0);

        data_high := data[:, '当日高价'];
    end

    highest := 0;
    num3 := 0;
    num5 := 0;
    num7 := 0;
    num10 := 0;
    num15 := 0;
    num30 := 0;
    num60 := 0;
    len := length(data);

    for i := len - 1 downto 0 do
    begin
        if data_high[i] > highest then
            highest := data_high[i];

        if i >= len - 3 then
            num3 := num5 := num7 := num10 := num15 := num30 := num60 := highest;
        else if i >= len - 5 then
            num5 := num7 := num10 := num15 := num30 := num60 := highest;
        else if i >= len - 7 then
            num7 := num10 := num15 := num30 := num60 := highest;
        else if i >= len - 10 then
            num10 := num15 := num30 := num60 := highest;
        else if i >= len - 15 then
            num15 := num30 := num60 := highest;
        else if i >= len - 30 then
            num30 := num60 := highest;
        else if i >= len - 60 then
            num60 := highest;
    end
    return array(num3, num5, num7, num10, num15, num30, num60);
end

function 计算买入(stock_name, stock_code, day);
begin
    buy_price := 0;
    buy_time := 0;
    buy_amount := 0;

    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
    begin
        当日涨停价 := StockZtClose(day);
    end

    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_1m()) do
    begin
        data := select
        TimeToStr(["date"]) as "时间",
        ["close"],
        ['amount'],
        ['open'],
        ['low']
        from markettable datekey day to day+0.99999 of DefaultStockID() end;
    end

    if data[0]['low'] <> 当日涨停价 and data[0]['close'] = 当日涨停价 then
        return array(当日涨停价, data[0]['时间'], 0, 0);

    涨停拉升 := 0;
    第一个非涨停价 := 0;
    for idx in data do
    begin
        if data[idx]['close'] <> 当日涨停价 then
        begin
            第一个非涨停价 := data[idx]['close'];
        end
        else
        begin
            if 第一个非涨停价 <> 0 then
            begin
                buy_price := data[idx]['close'];
                buy_time := data[idx]['时间'];

                while True do
                begin
                    if idx = 0 then
                        break;
                    if data[idx]['close'] >= data[idx - 1]['close'] then
                        idx -= 1;
                    else
                        break;
                end
                涨停拉升 := count_ratio(当日涨停价, data[idx]['close']);
                break;
            end
        end
        buy_amount += data[idx]['amount'];
    end
    return array(buy_price, buy_time, int(buy_amount/10000), 涨停拉升);
end


function 计算涨停板(stock_code, day);
begin
    num1 := 0;
    num2 := 0;
    num3 := 0;
    num4 := 0;
    num5 := 0;
    num6 := 0;
    num7 := 0;
    num10 := 0;
    num15 := 0;
    num30 := 0;

    num := 0;
    with *,array(pn_Stock():stock_code, pn_date():day, pn_rate():2, pn_rateday():day, PN_Cycle():cy_day()) do
    begin
        ret := 0;
        for i := 1 to 30 do
        begin
            one_day := StockEndTPrevNDay(day, i);
            str_one_day := DateToStr(one_day);
            if StockIsZt(one_day) then
                num += 1;

            if i = 1 then
                num1 := num;
            else if i = 2 then
                num2 := num;
            else if i = 3 then
                num3 := num;
            else if i = 4 then
                num4 := num;
            else if i = 5 then
                num5 := num;
            else if i = 6 then
                num6 := num;
            else if i = 7 then
                num7 := num;
            else if i = 10 then
                num10 := num;
            else if i = 15 then
                num15 := num;
            else if i = 30 then
                num30 := num;
        end
        return array(num1, num2, num3, num4, num5, num6, num7, num10, num15, num30);
    end
end

function count_ratio(value1, value2);
begin
    if value2 = 0 then
        return 0;
    return floatn((value1 / value2 - 1) * 100, 3);
end

Function is_trade_day(day,stock_code);
Begin
    with *,array(pn_Stock():stock_code,PN_Date():day,pn_rate():0,pn_rateday():day,PN_Cycle():"日线") do
    begin
        if not spec(isTradeDay(day),stock_code) then
            return false;

        if IsStockGoDelistingPeriod(day) then
            return false;

        if IsST_3(day)=1 then
            return false
    end
    return true;
End;
