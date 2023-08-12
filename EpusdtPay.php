<?php
namespace App\Payments;
class EpusdtPay {
    public function __construct($config)
    {
        $this->config = $config;
    }

    public function form()
    {
        return [
            'url' => [
                'label' => 'Url',
                'description' => 'Epusdt Api Url',
                'type' => 'input',
            ],
            'apitoken' => [
                'label' => 'ApiToken',
                'description' => 'Epusdt Api Token',
                'type' => 'input',
            ]
        ];
    }

    public function pay($order)
    {
        $params = [
            'amount' => $order['total_amount']/100,
            'order_id' => $order['trade_no'],
            'notify_url' => $order['notify_url'],
            'redirect_url' => $order['return_url'],
        ];
        $params['signature'] = $this->getSign($params, $this->config['apitoken']);
        $client = [
            'http' => [
                'method'  => 'POST',
                'header' => 'Content-Type:application/json',
                'content' => json_encode($params),
            ]
        ];
        $context  = stream_context_create($client);
        $response = file_get_contents($this->config['url'] . '/api/v1/order/create-transaction', false, $context);
        $body = json_decode($response, true);
        if($body['status_code'] != 200){
            abort(500, $body['message']);
        }
        $url = $body['data']['payment_url']; //RedirectUrl
        $qr = $body['data']['token']; //QrCode
        return [
            'type' => 1, // 0 -> QrCode 1 -> RedirectUrl
            'data' => $url,
        ];
    }

    private function getSign(array $parameter, string $signKey)
    {
        ksort($parameter);
        reset($parameter);
        $sign = '';
        $urls = '';
        foreach ($parameter as $key => $val) {
            if ($val == '') continue;
            if ($key != 'signature') {
                if ($sign != '') {
                    $sign .= "&";
                    $urls .= "&";
                }
                $sign .= "$key=$val";
                $urls .= "$key=" . urlencode($val);
            }
        }
        $sign = md5($sign . $signKey);
        return $sign;
    }
    
    public function notify($params)
    {
        $sign = $params['signature'];
        $signature = $this->getSign($params, $this->config['apitoken']);
        if ($sign !== $signature) {
            return false;
        }
        return [
            'trade_no' => $params['order_id'],
            'callback_no' => $params['trade_id']
        ];
    }
}
