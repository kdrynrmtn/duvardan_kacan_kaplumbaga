import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose


class DuvarKontrol(Node):

    def __init__(self):
        super().__init__('duvar_kontrol')

        # ROS 2 parametreleri
        self.declare_parameter('hareket_hizi', 1.5)
        self.declare_parameter('donus_hizi', 1.5)
        self.declare_parameter('alt_sinir', 1.0)
        self.declare_parameter('ust_sinir', 10.0)

        # Kaplumbağanın son konumunu saklayacağız.
        self.x = 5.5
        self.y = 5.5
        self.aci = 0.0

        # Dönüş durumunu takip ediyoruz.
        self.donuyor = False
        self.hedef_aci = 0.0

        # Konum bilgilerini okuyan abone.
        self.abone = self.create_subscription(
            Pose,
            '/turtle1/pose',
            self.konum_geldi,
            10
        )

        # Hız komutu göndermek için yayıncı.
        self.yayinci = self.create_publisher(
            Twist,
            '/turtle1/cmd_vel',
            10
        )

        # Her saniye konumu yazdıran zamanlayıcı.
        self.zamanlayici = self.create_timer(
            1.0,
            self.konum_yazdir
        )

        self.get_logger().info(
            'Duvar kontrol dugumu baslatildi.'
        )

    def konum_geldi(self, mesaj):
        # Güncel konumu sakla.
        self.x = mesaj.x
        self.y = mesaj.y
        self.aci = mesaj.theta

        # Güncel parametre değerlerini oku.
        hareket_hizi = self.get_parameter(
            'hareket_hizi'
        ).value

        donus_hizi = self.get_parameter(
            'donus_hizi'
        ).value

        alt_sinir = self.get_parameter(
            'alt_sinir'
        ).value

        ust_sinir = self.get_parameter(
            'ust_sinir'
        ).value

        twist = Twist()

        # Duvara yaklaşınca dönüş moduna geç.
        if not self.donuyor and (
            self.x < alt_sinir or self.x > ust_sinir or
            self.y < alt_sinir or self.y > ust_sinir
        ):
            self.donuyor = True

            # Mevcut yönün tersini hedefle.
            self.hedef_aci = self.aci + math.pi

            # Hedef açıyı -pi ile pi arasına getir.
            while self.hedef_aci > math.pi:
                self.hedef_aci -= 2.0 * math.pi

            while self.hedef_aci < -math.pi:
                self.hedef_aci += 2.0 * math.pi

            self.get_logger().info(
                'Duvara yaklasildi, yon degistiriliyor.'
            )

        if self.donuyor:
            # Hedef açıyla mevcut açı arasındaki fark.
            aci_farki = self.hedef_aci - self.aci

            # En kısa dönüş yönünü belirle.
            while aci_farki > math.pi:
                aci_farki -= 2.0 * math.pi

            while aci_farki < -math.pi:
                aci_farki += 2.0 * math.pi

            if abs(aci_farki) > 0.08:
                # Dönüş sırasında ileri veya geri gitme.
                twist.linear.x = 0.0

                if aci_farki > 0:
                    twist.angular.z = donus_hizi
                else:
                    twist.angular.z = -donus_hizi

            else:
                # Dönüş tamamlandı.
                self.donuyor = False
                twist.linear.x = hareket_hizi
                twist.angular.z = 0.0

                self.get_logger().info(
                    'Yon degisti, ileri hareket ediliyor.'
                )

        else:
            # Güvenli alanda ileri git.
            twist.linear.x = hareket_hizi
            twist.angular.z = 0.0

        self.yayinci.publish(twist)

    def konum_yazdir(self):
        # Her saniye güncel konumu terminale yazdır.
        self.get_logger().info(
            f'Kaplumbaga konumu: X={self.x:.2f}, Y={self.y:.2f}'
        )


def main(args=None):
    rclpy.init(args=args)

    dugum = DuvarKontrol()

    try:
        rclpy.spin(dugum)

    except KeyboardInterrupt:
        pass

    finally:
        # Düğüm kapanırken durma komutu gönder.
        durdur = Twist()
        dugum.yayinci.publish(durdur)

        dugum.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
