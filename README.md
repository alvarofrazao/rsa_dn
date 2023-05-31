# rsa_dn


primeiro putval:

mem = id*100 + val (ou val*2)

segundo putval:

mem = (mem/100) * 10000 + ((mem%100)+val) + id*100


core pega numa posiçao inicial e calcula a area a patrulhar, divide em 2*n celulas, sendo n o numero de drones (2 celulas por drone) e calcula o centro de cada uma
nota: havera entre 4/6 posiçoes iniciais por onde o core ira começar a calcular a area

atribui a cada drone uma celula e envia pelo broker o centro da celula atribuida a cada drone

drone calcula o trajeto da sua posiçao atual para o destino

no destino, incrementa de x em x segundos ate um certo limite, quando o limite for atingido, o drone retorna para o core

processo repete-se ate todas as celulas terem sido vistas ou, se quando todos os drones já tiverem visto uma celula e tiverem sido feitas
menos de k deteçoes, entao muda-se de area