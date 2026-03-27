import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Heart, Users, Eye, Sparkles, ArrowRight } from 'lucide-react';
import SEO from '../components/SEO';

const fadeUp = { hidden: { opacity: 0, y: 24 }, visible: { opacity: 1, y: 0 } };

const About = () => {
  return (
    <div className="min-h-screen pt-20" data-testid="about-page">
      <SEO 
        title="Sobre a 4Luis"
        description="A 4Luis nasceu de um sonho simples: viajar mais, conhecer o mundo e viver experiências reais. Descobre como funciona a nossa plataforma de CrowdDreaming."
      />
      {/* Hero */}
      <section className="py-16 md:py-24 bg-gradient-to-b from-[#FAFAF9] to-white">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <motion.div initial="hidden" animate="visible" variants={fadeUp} transition={{ duration: 0.6 }}>
            <span className="inline-block px-4 py-2 bg-[#FFBE98]/15 rounded-full text-[#E6A07C] font-medium text-sm mb-6">
              Sobre a 4Luis
            </span>
            <h1 className="text-4xl sm:text-5xl font-bold text-[#2D2A26] mb-6 leading-tight">
              De onde surgiu esta ideia?
            </h1>
            <div className="space-y-4 text-lg text-[#6B6661] leading-relaxed">
              <p>
                A 4Luis nasceu de um sonho simples:<br />
                <span className="text-[#2D2A26] font-medium">viajar mais, conhecer o mundo e viver experiências reais.</span>
              </p>
              <p>
                Mas também nasceu de uma pergunta:<br />
                <span className="font-handwritten text-4xl text-[#FFBE98]">afinal, e se as nossas viagens de sonho se pudessem realizar...</span>
              </p>
              <p>
                E se fosse possível criar uma comunidade<br />
                onde as pessoas ajudam outras a realizar os seus sonhos?
              </p>
            </div>
          </motion.div>
        </div>
      </section>

      {/* O que é */}
      <section className="py-16 bg-white">
        <div className="max-w-3xl mx-auto px-6">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp} transition={{ duration: 0.6 }}>
            <h2 className="text-3xl font-bold text-[#2D2A26] mb-6">O que é a 4Luis?</h2>
            <p className="text-lg text-[#6B6661] leading-relaxed mb-6">
              A 4Luis é uma plataforma de <span className="font-semibold text-[#2D2A26]">CrowdDreaming</span>.<br />
              Um espaço onde:
            </p>
            <ul className="space-y-3 mb-8">
              {[
                'pessoas apoiam viagens de sonho',
                'partilham experiências',
                'e fazem parte de algo maior'
              ].map((item) => (
                <li key={item} className="flex items-start gap-3 text-[#6B6661]">
                  <Heart className="w-4 h-4 text-[#FFBE98] mt-1 flex-shrink-0" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
            <p className="text-[#6B6661] leading-relaxed">
              Não é apenas sobre financiar viagens.<br />
              É sobre acreditar que <span className="font-handwritten text-2xl text-[#FFBE98]">os sonhos se podem tornar realidade quando são partilhados.</span>
            </p>
          </motion.div>
        </div>
      </section>

      {/* Como funciona */}
      <section className="py-16 bg-[#FAFAF9]">
        <div className="max-w-3xl mx-auto px-6">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp} transition={{ duration: 0.6 }}>
            <h2 className="text-3xl font-bold text-[#2D2A26] mb-8">Como funciona?</h2>
            <div className="space-y-6 text-[#6B6661] leading-relaxed text-lg">
              <p>Um sonhador partilha um sonho.</p>
              <p>Outras pessoas podem contribuir para esse sonho.</p>
              <p>
                Ao participar e convidar outros,<br />
                também ganhas a possibilidade de realizar o teu próprio sonho.
              </p>
            </div>
            <div className="mt-10 flex items-center justify-center gap-4 text-[#2D2A26] font-semibold">
              <span className="px-4 py-2 bg-[#FFBE98]/15 rounded-xl text-sm">apoiar</span>
              <ArrowRight className="w-4 h-4 text-[#FFBE98]" />
              <span className="px-4 py-2 bg-[#FFBE98]/15 rounded-xl text-sm">partilhar</span>
              <ArrowRight className="w-4 h-4 text-[#FFBE98]" />
              <span className="px-4 py-2 bg-[#FFBE98]/15 rounded-xl text-sm">realizar</span>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Confiança */}
      <section className="py-16 bg-white">
        <div className="max-w-3xl mx-auto px-6">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp} transition={{ duration: 0.6 }}>
            <h2 className="text-3xl font-bold text-[#2D2A26] mb-8">Porque podes confiar?</h2>
            <p className="text-[#6B6661] mb-8">A 4Luis foi construída com base em três princípios:</p>
            <div className="grid gap-6 md:grid-cols-3">
              {[
                {
                  icon: Eye,
                  title: 'Transparência',
                  text: 'A plataforma não cobra nenhuma comissão, as contribuições vão diretamente para a conta bancária indicada pelos membros.'
                },
                {
                  icon: Users,
                  title: 'Comunidade',
                  text: 'Cada sonho cresce com o apoio de outras pessoas.'
                },
                {
                  icon: Heart,
                  title: 'Autenticidade',
                  text: 'Não existem promessas irreais — apenas pessoas reais.'
                }
              ].map(({ icon: Icon, title, text }) => (
                <div key={title} className="bg-[#FAFAF9] rounded-2xl p-6">
                  <Icon className="w-6 h-6 text-[#FFBE98] mb-3" />
                  <h3 className="font-bold text-[#2D2A26] mb-2">{title}</h3>
                  <p className="text-sm text-[#6B6661] leading-relaxed">{text}</p>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* A viagem começa aqui */}
      <section className="py-16 bg-[#FAFAF9]">
        <div className="max-w-3xl mx-auto px-6">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp} transition={{ duration: 0.6 }}>
            <h2 className="text-3xl font-bold text-[#2D2A26] mb-6">A viagem começa aqui</h2>
            <div className="space-y-4 text-lg text-[#6B6661] leading-relaxed">
              <p>
                A primeira viagem a ser financiada é a viagem do <span className="font-semibold text-[#2D2A26]">Luis</span>, o fundador.
              </p>
              <div className="flex items-center gap-3 py-2">
                <div className="w-10 h-10 rounded-full bg-[#FFBE98]/20 flex items-center justify-center text-[#FFBE98] font-bold text-sm">L</div>
                <div>
                  <p className="text-sm font-semibold text-[#2D2A26]">Luis</p>
                  <p className="text-xs text-[#6B6661]">Membro desde 2026 · Criador da 4Luis</p>
                </div>
              </div>
              <p>Mas este é apenas o começo.</p>
              <p>
                O objetivo é criar uma comunidade de sonhadores<br />
                onde cada pessoa pode, um dia, ver o seu sonho tornar-se realidade.
              </p>
            </div>
          </motion.div>
        </div>
      </section>

      {/* CTA Final */}
      <section className="py-20 bg-gradient-to-b from-white to-[#FAFAF9]">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp} transition={{ duration: 0.6 }}>
            <Sparkles className="w-8 h-8 text-[#FFBE98] mx-auto mb-4" />
            <h2 className="text-3xl font-bold text-[#2D2A26] mb-4">Sonha connosco</h2>
            <p className="text-lg text-[#6B6661] leading-relaxed mb-8">
              Se acreditas que os sonhos podem ser partilhados,<br />
              então já fazes parte disto.
            </p>
            <Link
              to="/"
              className="inline-flex items-center gap-2 px-8 py-4 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-bold text-lg hover:bg-[#FFAB7D] transition-colors"
              data-testid="about-cta-btn"
            >
              <Heart className="w-5 h-5" />
              Contribuir para este sonho
            </Link>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default About;
