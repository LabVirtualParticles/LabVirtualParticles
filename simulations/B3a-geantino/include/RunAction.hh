//
// ********************************************************************
// * License and Disclaimer                                           *
// *                                                                  *
// * The  Geant4 software  is  copyright of the Copyright Holders  of *
// * the Geant4 Collaboration.  It is provided  under  the terms  and *
// * conditions of the Geant4 Software License,  included in the file *
// * LICENSE and available at  http://cern.ch/geant4/license .  These *
// * include a list of copyright holders.                             *
// *                                                                  *
// * Neither the authors of this software system, nor their employing *
// * institutes,nor the agencies providing financial support for this *
// * work  make  any representation or  warranty, express or implied, *
// * regarding  this  software system or assume any liability for its *
// * use.  Please see the license in the file  LICENSE  and URL above *
// * for the full disclaimer and the limitation of liability.         *
// *                                                                  *
// * This  code  implementation is the result of  the  scientific and *
// * technical work of the GEANT4 collaboration.                      *
// * By using,  copying,  modifying or  distributing the software (or *
// * any work based  on the software)  you  agree  to acknowledge its *
// * use  in  resulting  scientific  publications,  and indicate your *
// * acceptance of all terms of the Geant4 Software license.          *
// ********************************************************************
//
/// \file B3/B3a/include/RunAction.hh
/// \brief Definition of the B3a::RunAction class
///
/// Modificado pelo Geantino Labs (IFPR), nov/2026: alem do resumo
/// original no terminal, a run agora grava os arquivos lidos pelo backend
/// do site, no diretorio de trabalho:
///   - geometria.gdml   (inicio da run)
///   - trajetorias.json (fim da run, via Geantino::TrajectoryRecorder)
///   - resultados.json  (fim da run: eventos, aniquilacoes "boas", dose,
///                       as linhas de resposta entre cristais e o espectro
///                       de energia nos cristais)

#ifndef B3aRunAction_h
#define B3aRunAction_h 1

#include "G4Accumulable.hh"
#include "G4ThreeVector.hh"
#include "G4UserRunAction.hh"
#include "globals.hh"

#include <vector>

class G4Run;

namespace B3a
{

/// Linha de resposta: os dois cristais acima do limiar num evento "bom"
struct LineOfResponse
{
    G4int event = 0;
    G4ThreeVector p1, p2;  // centros dos cristais (referencial do mundo)
    G4double e1 = 0., e2 = 0.;  // energia depositada em cada cristal
};

/// Run action class

class RunAction : public G4UserRunAction
{
  public:
    RunAction();
    ~RunAction() override = default;

    void BeginOfRunAction(const G4Run*) override;
    void EndOfRunAction(const G4Run*) override;

    void CountEvent() { fGoodEvents += 1; };
    void SumDose(G4double dose) { fSumDose += dose; };
    void AddLineOfResponse(const LineOfResponse& lor) { fLines.push_back(lor); }
    // Espectro: energia depositada em cada cristal atingido (todos os
    // eventos, nao so as coincidencias), em faixas de kSpectrumBin.
    void AddCrystalHit(G4double edep);

    static constexpr G4double kSpectrumBinkeV = 10.;
    static constexpr G4int kSpectrumBins = 110;  // 0 a 1100 keV

  private:
    void WriteResultsJSON(const G4Run* run) const;

    G4Accumulable<G4int> fGoodEvents = 0;
    G4Accumulable<G4double> fSumDose = 0.;
    std::vector<LineOfResponse> fLines;
    std::vector<G4int> fSpectrum = std::vector<G4int>(kSpectrumBins, 0);
    G4int fSpectrumOverflow = 0;
};

}  // namespace B3a

#endif
