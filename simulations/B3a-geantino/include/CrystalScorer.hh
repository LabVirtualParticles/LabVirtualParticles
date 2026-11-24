/// \file CrystalScorer.hh
/// \brief Scorer de energia por cristal individual (anel + posicao no anel)
///
/// Geantino Labs (IFPR), nov/2026. Nao existe no exemplo original.
///
/// O B3a original registra a energia nos cristais com G4PSEnergyDeposit,
/// cujo indice e so o numero de copia do cristal dentro do anel (0..31):
/// o mesmo cristal dos 9 aneis cai no mesmo indice. Isso fica como esta
/// (e o que decide os eventos "bons" no EventAction, igual ao original).
///
/// Este scorer e um segundo primitivo, registrado no mesmo detector, que
/// separa tambem o anel (indice = anel * 100 + cristal) e guarda o centro
/// de cada cristal no referencial do mundo. Serve so para desenhar no
/// site as linhas de resposta (LOR) entre os dois cristais atingidos.

#ifndef GeantinoCrystalScorer_h
#define GeantinoCrystalScorer_h 1

#include "G4PSEnergyDeposit.hh"
#include "G4ThreeVector.hh"

#include <map>

namespace Geantino
{

class CrystalScorer : public G4PSEnergyDeposit
{
  public:
    explicit CrystalScorer(const G4String& name) : G4PSEnergyDeposit(name) {}
    ~CrystalScorer() override = default;

    // Centro do cristal (referencial do mundo) para um indice ja visto
    static bool CentreOf(G4int index, G4ThreeVector& centre);

  protected:
    G4int GetIndex(G4Step* step) override;

  private:
    static std::map<G4int, G4ThreeVector> fCentres;
};

}  // namespace Geantino

#endif
